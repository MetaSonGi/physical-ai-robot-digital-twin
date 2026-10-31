"""Replays a recorded episode as /joint_states (and /leader/joint_states) at its original timing.

Lets you develop the Unity twin and dashboards without any robot attached.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

ARM = ["joint1", "joint2", "joint3", "joint4"]


class Replayer(Node):
    def __init__(self):
        super().__init__("episode_replayer")
        self.declare_parameter("episode", "")
        self.declare_parameter("loop", True)
        self.declare_parameter("gripper_joint", "gripper_left_joint")
        g = self.get_parameter
        ep = np.load(g("episode").value)
        self.t, self.obs, self.act = ep["t"], ep["obs"], ep["action"]
        self.loop, self.gj = g("loop").value, g("gripper_joint").value
        self.i = 0
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.lpub = self.create_publisher(JointState, "/leader/joint_states", 10)
        dt = float(np.median(np.diff(self.t))) if len(self.t) > 1 else 0.05
        self.create_timer(dt, self.tick)

    def tick(self):
        if self.i >= len(self.obs):
            if not self.loop:
                return
            self.i = 0
        stamp = self.get_clock().now().to_msg()
        for pub, arr in ((self.pub, self.obs), (self.lpub, self.act)):
            m = JointState(name=ARM + [self.gj], position=arr[self.i].astype(float).tolist())
            m.header.stamp = stamp
            pub.publish(m)
        self.i += 1


def main():
    rclpy.init()
    rclpy.spin(Replayer())
    rclpy.shutdown()
