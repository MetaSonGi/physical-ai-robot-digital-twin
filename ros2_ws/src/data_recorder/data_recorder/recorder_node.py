"""Demonstration recorder.

Samples follower /joint_states (obs) and leader /leader/joint_states (action) at a fixed
rate and writes datasets/<task>/episode_XXXX.npz (format: learning/dataset.py).

  ros2 service call /recorder/start std_srvs/srv/Trigger
  ros2 service call /recorder/stop  std_srvs/srv/Trigger      # saves (success=True)
  ros2 service call /recorder/discard std_srvs/srv/Trigger    # drop current episode
"""
import glob
import os
import time

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray
from std_srvs.srv import Trigger

ARM = ["joint1", "joint2", "joint3", "joint4"]


class Recorder(Node):
    def __init__(self):
        super().__init__("data_recorder")
        self.declare_parameter("out_dir", os.path.expanduser("~/physical-ai-robot-digital-twin/datasets/pick_place"))
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("follower_gripper_joint", "gripper_left_joint")
        self.declare_parameter("leader_gripper_joint", "gripper_joint")
        self.declare_parameter("gripper_scale", 1.0)
        g = self.get_parameter
        self.out_dir = g("out_dir").value
        os.makedirs(self.out_dir, exist_ok=True)
        self.fg, self.lg, self.scale = g("follower_gripper_joint").value, g("leader_gripper_joint").value, g("gripper_scale").value
        self.follower = self.leader = None
        self.context = None
        self.recording, self.buf = False, []
        self.create_subscription(JointState, "/joint_states", lambda m: setattr(self, "follower", self._vec(m, self.fg, 1.0)), 10)
        self.create_subscription(JointState, "/leader/joint_states", lambda m: setattr(self, "leader", self._vec(m, self.lg, self.scale)), 10)
        self.create_subscription(Float32MultiArray, "/task/context", lambda m: setattr(self, "context", np.array(m.data, np.float32)), 10)
        self.create_service(Trigger, "/recorder/start", self.start)
        self.create_service(Trigger, "/recorder/stop", self.stop)
        self.create_service(Trigger, "/recorder/discard", self.discard)
        self.create_timer(1.0 / g("rate_hz").value, self.tick)

    @staticmethod
    def _vec(msg, gripper, scale):
        idx = {n: i for i, n in enumerate(msg.name)}
        if not all(j in idx for j in ARM) or gripper not in idx:
            return None
        return np.array([msg.position[idx[j]] for j in ARM] + [msg.position[idx[gripper]] * scale], np.float32)

    def tick(self):
        if self.recording and self.follower is not None and self.leader is not None:
            self.buf.append((time.monotonic(), self.follower.copy(), self.leader.copy()))

    def start(self, _req, res):
        self.buf, self.recording = [], True
        res.success, res.message = True, "recording"
        return res

    def discard(self, _req, res):
        self.buf, self.recording = [], False
        res.success, res.message = True, "discarded"
        return res

    def stop(self, _req, res):
        self.recording = False
        if len(self.buf) < 2:
            res.success, res.message = False, "no samples (are both leader and follower publishing?)"
            return res
        t = np.array([b[0] for b in self.buf]); t -= t[0]
        data = {"t": t, "obs": np.stack([b[1] for b in self.buf]), "action": np.stack([b[2] for b in self.buf]),
                "success": np.array(True)}
        if self.context is not None:
            data["context"] = self.context
        n = len(glob.glob(os.path.join(self.out_dir, "episode_*.npz")))
        path = os.path.join(self.out_dir, f"episode_{n:04d}.npz")
        np.savez(path, **data)
        res.success, res.message = True, f"saved {len(t)} frames -> {path}"
        self.get_logger().info(res.message)
        return res


def main():
    rclpy.init()
    rclpy.spin(Recorder())
    rclpy.shutdown()
