"""Hardware-free follower: integrates arm/gripper commands with first-order dynamics and
publishes /joint_states. Optionally seeds start pose and /task/context from a recorded episode.

Same dynamics as learning/generate_synthetic.py, so sim results match offline evaluation.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray
from trajectory_msgs.msg import JointTrajectory

ARM = ["joint1", "joint2", "joint3", "joint4"]


class SimFollower(Node):
    def __init__(self):
        super().__init__("sim_follower")
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("gain", 0.5)
        self.declare_parameter("gripper_joint", "gripper_left_joint")
        self.declare_parameter("episode", "")
        g = self.get_parameter
        self.gain, self.gj = g("gain").value, g("gripper_joint").value
        self.q = np.array([0.0, -1.0, 0.3, 0.7, 0.01])
        self.context = None
        if g("episode").value:
            ep = np.load(g("episode").value)
            self.q = ep["obs"][0].astype(float)
            if "context" in ep.files:
                self.context = ep["context"].astype(np.float32)
        self.cmd = self.q.copy()
        self.create_subscription(JointTrajectory, "/arm_controller/joint_trajectory", self.on_arm, 10)
        self.create_subscription(JointState, "/gripper/command", self.on_grip, 10)
        self.js_pub = self.create_publisher(JointState, "/joint_states", 10)
        self.ctx_pub = self.create_publisher(Float32MultiArray, "/task/context", 10)
        self.create_timer(1.0 / g("rate_hz").value, self.tick)

    def on_arm(self, msg):
        if msg.points:
            idx = {n: i for i, n in enumerate(msg.joint_names)}
            for k, j in enumerate(ARM):
                if j in idx:
                    self.cmd[k] = msg.points[-1].positions[idx[j]]

    def on_grip(self, msg):
        if msg.position:
            self.cmd[4] = msg.position[0]

    def tick(self):
        self.q = self.q + self.gain * (self.cmd - self.q)
        js = JointState(name=ARM + [self.gj], position=self.q.tolist())
        js.header.stamp = self.get_clock().now().to_msg()
        self.js_pub.publish(js)
        if self.context is not None:
            self.ctx_pub.publish(Float32MultiArray(data=self.context.tolist()))


def main():
    rclpy.init()
    rclpy.spin(SimFollower())
    rclpy.shutdown()
