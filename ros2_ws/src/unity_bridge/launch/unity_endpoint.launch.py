"""ROS-TCP endpoint for Unity (package: ros_tcp_endpoint, branch main-ros2) + telemetry."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("ros_ip", default_value="0.0.0.0"),
        DeclareLaunchArgument("ros_tcp_port", default_value="10000"),
        Node(package="ros_tcp_endpoint", executable="default_server_endpoint", output="screen",
             parameters=[{"ROS_IP": LaunchConfiguration("ros_ip"),
                          "ROS_TCP_PORT": LaunchConfiguration("ros_tcp_port")}]),
        Node(package="unity_bridge", executable="twin_telemetry", output="screen"),
    ])
