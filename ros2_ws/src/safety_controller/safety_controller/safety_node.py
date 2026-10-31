"""safety_node: /policy/joint_target -> SafetyFilter -> arm & gripper controllers."""
import time

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from safety_controller.safety_filter import SafetyConfig, SafetyFilter

ARM = ["joint1", "joint2", "joint3", "joint4"]


class SafetyNode(Node):
    def __init__(self):
        super().__init__("safety_controller")
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("arm_command_topic", "/arm_controller/joint_trajectory")
        self.declare_parameter("gripper_command_topic", "/gripper/command")
        self.declare_parameter("gripper_joint", "gripper_left_joint")
        self.declare_parameter("timeout_s", 0.3)
        self.rate = self.get_parameter("rate_hz").value
        self.gripper_joint = self.get_parameter("gripper_joint").value
        self.filter = SafetyFilter(SafetyConfig(timeout_s=self.get_parameter("timeout_s").value))
        self.current = None
        self.target, self.target_stamp = None, 0.0

        self.create_subscription(JointState, "/joint_states", self.on_state, 10)
        self.create_subscription(JointState, "/policy/joint_target", self.on_target, 10)
        self.create_subscription(Bool, "/safety/estop", lambda m: self.filter.set_estop(m.data), 10)
        self.arm_pub = self.create_publisher(JointTrajectory, self.get_parameter("arm_command_topic").value, 10)
        self.grip_pub = self.create_publisher(JointState, self.get_parameter("gripper_command_topic").value, 10)
        self.status_pub = self.create_publisher(String, "/safety/status", 10)
        self.create_timer(1.0 / self.rate, self.tick)

    def _vec(self, msg: JointState):
        idx = {n: i for i, n in enumerate(msg.name)}
        names = ARM + [self.gripper_joint]
        if not all(n in idx for n in names):
            return None
        return np.array([msg.position[idx[n]] for n in names])

    def on_state(self, msg):
        v = self._vec(msg)
        if v is not None:
            self.current = v

    def on_target(self, msg):
        self.target, self.target_stamp = self._vec(msg), time.monotonic()

    def tick(self):
        if self.current is None:
            return
        res = self.filter.step(self.current, self.target, time.monotonic() - self.target_stamp, 1.0 / self.rate)
        self.status_pub.publish(String(data=res.status))
        traj = JointTrajectory(joint_names=ARM)
        dt = 1.0 / self.rate
        traj.points = [JointTrajectoryPoint(positions=res.command[:4].tolist(),
                                            time_from_start=Duration(sec=0, nanosec=int(dt * 1e9)))]
        self.arm_pub.publish(traj)
        self.grip_pub.publish(JointState(name=[self.gripper_joint], position=[float(res.command[4])]))


def main():
    rclpy.init()
    rclpy.spin(SafetyNode())
    rclpy.shutdown()
