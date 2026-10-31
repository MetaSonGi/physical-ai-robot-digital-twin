"""Policy inference node: /joint_states (+ /task/context) -> BCPolicy -> /policy/joint_target.

Requires the repo's `learning` package on PYTHONPATH (scripts/run_demo.sh sets it).
The output is a *target*, not a motor command: safety_controller decides what is executed.
"""
import collections
import time

import numpy as np
import rclpy
import torch
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32, Float32MultiArray

from learning.models import BCPolicy

ARM = ["joint1", "joint2", "joint3", "joint4"]


class PolicyNode(Node):
    def __init__(self):
        super().__init__("policy_inference")
        self.declare_parameter("checkpoint", "runs/bc_default/best.pt")
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("gripper_joint", "gripper_left_joint")
        g = self.get_parameter
        self.model = BCPolicy.load(g("checkpoint").value)
        self.gj = g("gripper_joint").value
        self.hist = collections.deque(maxlen=self.model.history)
        self.state, self.context = None, None
        self.create_subscription(JointState, "/joint_states", self.on_state, 10)
        self.create_subscription(Float32MultiArray, "/task/context",
                                 lambda m: setattr(self, "context", np.array(m.data, np.float32)), 10)
        self.pub = self.create_publisher(JointState, "/policy/joint_target", 10)
        self.lat_pub = self.create_publisher(Float32, "/policy/latency_ms", 10)
        self.create_timer(1.0 / g("rate_hz").value, self.tick)
        self.get_logger().info(f"loaded policy {self.model.config()}")

    def on_state(self, msg):
        idx = {n: i for i, n in enumerate(msg.name)}
        if all(j in idx for j in ARM + [self.gj]):
            self.state = np.array([msg.position[idx[j]] for j in ARM + [self.gj]], np.float32)

    def tick(self):
        if self.state is None:
            return
        obs = self.state if self.context is None else np.r_[self.state, self.context]
        if obs.shape[0] != self.model.obs_dim:
            self.get_logger().warn(f"obs dim {obs.shape[0]} != model {self.model.obs_dim} (missing /task/context?)",
                                   throttle_duration_sec=2.0)
            return
        self.hist.append(obs)
        while len(self.hist) < self.model.history:
            self.hist.appendleft(obs)
        t0 = time.perf_counter()
        target = self.model.predict(torch.from_numpy(np.stack(self.hist)[None]))[0].numpy()
        self.lat_pub.publish(Float32(data=(time.perf_counter() - t0) * 1e3))
        msg = JointState(name=ARM + [self.gj], position=target.astype(float).tolist())
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(PolicyNode())
    rclpy.shutdown()
