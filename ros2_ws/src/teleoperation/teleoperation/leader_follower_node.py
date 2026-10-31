"""Leader -> follower relay.

The leader arm is back-drivable (torque off) and publishes /leader/joint_states.
This node mirrors it onto the follower's arm controller and gripper.
If your OMX driver already provides a leader/follower launch, run that instead and keep
only the data_recorder; this node is useful for custom leaders (e.g. XR / Unity controller).
"""
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM = ["joint1", "joint2", "joint3", "joint4"]


class LeaderFollower(Node):
    def __init__(self):
        super().__init__("leader_follower")
        self.declare_parameter("leader_topic", "/leader/joint_states")
        self.declare_parameter("arm_command_topic", "/arm_controller/joint_trajectory")
        self.declare_parameter("gripper_command_topic", "/gripper/command")
        self.declare_parameter("leader_gripper_joint", "gripper_joint")
        self.declare_parameter("follower_gripper_joint", "gripper_left_joint")
        self.declare_parameter("gripper_scale", 1.0)  # map leader trigger range -> follower gripper range
        self.declare_parameter("time_from_start", 0.1)
        g = self.get_parameter
        self.lg, self.fg = g("leader_gripper_joint").value, g("follower_gripper_joint").value
        self.scale, self.tfs = g("gripper_scale").value, g("time_from_start").value
        self.arm_pub = self.create_publisher(JointTrajectory, g("arm_command_topic").value, 10)
        self.grip_pub = self.create_publisher(JointState, g("gripper_command_topic").value, 10)
        self.create_subscription(JointState, g("leader_topic").value, self.on_leader, 10)

    def on_leader(self, msg: JointState):
        idx = {n: i for i, n in enumerate(msg.name)}
        if not all(j in idx for j in ARM):
            return
        traj = JointTrajectory(joint_names=ARM)
        sec = int(self.tfs)
        traj.points = [JointTrajectoryPoint(positions=[msg.position[idx[j]] for j in ARM],
                                            time_from_start=Duration(sec=sec, nanosec=int((self.tfs - sec) * 1e9)))]
        self.arm_pub.publish(traj)
        if self.lg in idx:
            self.grip_pub.publish(JointState(name=[self.fg], position=[msg.position[idx[self.lg]] * self.scale]))


def main():
    rclpy.init()
    rclpy.spin(LeaderFollower())
    rclpy.shutdown()
