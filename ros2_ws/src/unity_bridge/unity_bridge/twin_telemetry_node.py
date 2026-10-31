"""Measures real-vs-twin sync: compares /joint_states with /unity/joint_states echoed back by Unity.

Publishes /twin/sync_error_rad (max-abs joint error) and /twin/latency_ms (stamp round-trip).
"""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32


class TwinTelemetry(Node):
    def __init__(self):
        super().__init__("twin_telemetry")
        self.real = {}
        self.create_subscription(JointState, "/joint_states", self.on_real, 10)
        self.create_subscription(JointState, "/unity/joint_states", self.on_twin, 10)
        self.err_pub = self.create_publisher(Float32, "/twin/sync_error_rad", 10)
        self.lat_pub = self.create_publisher(Float32, "/twin/latency_ms", 10)

    def on_real(self, msg):
        self.real = dict(zip(msg.name, msg.position))

    def on_twin(self, msg):
        common = [n for n in msg.name if n in self.real]
        if common:
            twin = dict(zip(msg.name, msg.position))
            err = max(abs(self.real[n] - twin[n]) for n in common)
            self.err_pub.publish(Float32(data=float(err)))
        if msg.header.stamp.sec or msg.header.stamp.nanosec:
            lat = (self.get_clock().now() - Time.from_msg(msg.header.stamp)).nanoseconds / 1e6
            self.lat_pub.publish(Float32(data=float(np.clip(lat, 0, 1e4))))


def main():
    rclpy.init()
    rclpy.spin(TwinTelemetry())
    rclpy.shutdown()
