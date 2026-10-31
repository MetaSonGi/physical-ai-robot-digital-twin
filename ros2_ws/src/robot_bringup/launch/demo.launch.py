"""One launch file, three modes.

  mode:=sim       sim_follower + policy + safety            (no hardware)
  mode:=replay    episode_replayer                          (Unity/dashboard development)
  mode:=hardware  policy + safety; start the OMX driver separately
  mode:=teleop    leader_follower + data_recorder           (collect demonstrations)

  unity:=true     also start ROS-TCP endpoint + twin telemetry
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    cfg = os.path.join(get_package_share_directory("robot_bringup"), "config", "robot.yaml")
    mode, ckpt, ep = LaunchConfiguration("mode"), LaunchConfiguration("checkpoint"), LaunchConfiguration("episode")
    is_ = lambda *m: IfCondition(PythonExpression(["'", mode, f"' in {list(m)}"]))  # noqa: E731

    return LaunchDescription([
        DeclareLaunchArgument("mode", default_value="sim"),
        DeclareLaunchArgument("checkpoint", default_value="runs/bc_default/best.pt"),
        DeclareLaunchArgument("episode", default_value=""),
        DeclareLaunchArgument("out_dir", default_value="datasets/pick_place"),
        DeclareLaunchArgument("unity", default_value="false"),

        Node(package="robot_bringup", executable="sim_follower", condition=is_("sim"),
             parameters=[cfg, {"episode": ep}]),
        Node(package="robot_bringup", executable="episode_replayer", condition=is_("replay"),
             parameters=[cfg, {"episode": ep}]),
        Node(package="policy_inference", executable="policy_node", condition=is_("sim", "hardware"),
             parameters=[cfg, {"checkpoint": ckpt}], output="screen"),
        Node(package="safety_controller", executable="safety_node", condition=is_("sim", "hardware"),
             parameters=[cfg], output="screen"),
        Node(package="teleoperation", executable="leader_follower", condition=is_("teleop"), parameters=[cfg]),
        Node(package="data_recorder", executable="recorder", condition=is_("teleop"),
             parameters=[cfg, {"out_dir": LaunchConfiguration("out_dir")}], output="screen"),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory("unity_bridge"), "launch", "unity_endpoint.launch.py")),
            condition=IfCondition(LaunchConfiguration("unity"))),
    ])
