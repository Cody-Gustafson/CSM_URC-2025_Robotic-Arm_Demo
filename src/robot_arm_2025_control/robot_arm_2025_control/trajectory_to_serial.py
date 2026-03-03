#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

import serial


class TrajectoryToSerial(Node):

    def __init__(self):
        super().__init__('trajectory_to_serial')

        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('trajectory_topic', '/arm_controller/joint_trajectory')
        self.declare_parameter('ack_timeout_sec', 1.0)

        serial_port_name = self.get_parameter('serial_port').get_parameter_value().string_value
        baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
        trajectory_topic = self.get_parameter('trajectory_topic').get_parameter_value().string_value
        self.ack_timeout_sec = self.get_parameter('ack_timeout_sec').get_parameter_value().double_value


        try:
            self.serial_port = serial.Serial(serial_port_name, baud_rate, timeout=self.ack_timeout_sec)
            time.sleep(2)
            self.get_logger().info(f"Serial connection established on {serial_port_name} @ {baud_rate} baud.")
        except Exception as exc:
            self.get_logger().error(f"Failed to open serial port '{serial_port_name}': {exc}")
            self.serial_port = None

        self.subscription = self.create_subscription(
            JointTrajectory,
            trajectory_topic,
            self.trajectory_callback,
            10,
        )

        self.get_logger().info(f"Listening for controller output on '{trajectory_topic}'.")

    def trajectory_callback(self, msg: JointTrajectory):
        if not msg.points:
            return

        self.get_logger().info(f"Received trajectory with {len(msg.points)} point(s).")
        previous_time = 0.0

        for point in msg.points:
            point_time = point.time_from_start.sec + point.time_from_start.nanosec * 1e-9
            sleep_time = max(0.0, point_time - previous_time)
            if sleep_time > 0.0:
                time.sleep(sleep_time)
            previous_time = point_time

            payload = self.convert_point_to_serial_message(msg.joint_names, point.positions)
            self.send_to_serial(payload)

    def convert_point_to_serial_message(self, joint_names, positions):
        joint_dict = dict(zip(joint_names, positions))

        j1 = joint_dict.get('J1', 0.0)
        j2 = joint_dict.get('J2', 0.0)
        j3 = joint_dict.get('J3', 0.0)
        j4 = joint_dict.get('J4', 0.0)
        j5 = joint_dict.get('J5', 0.0)

        motor_j1 = j1
        motor_j2 = j2
        motor_j3 = -(j3 + j2)
        motor_j4 = j4
        motor_j5 = j5

        rad_to_deg = 180.0 / math.pi
        servo_values = [
            motor_j1 * rad_to_deg + 90.0,
            motor_j2 * rad_to_deg + 90.0,
            motor_j3 * rad_to_deg + 90.0,
            motor_j4 * rad_to_deg + 90.0,
            motor_j5 * rad_to_deg + 90.0,
        ]

        clamped = [min(max(value, 0.0), 180.0) for value in servo_values]
        return f"{clamped[0]:.2f},{clamped[1]:.2f},{clamped[2]:.2f},{clamped[3]:.2f},{clamped[4]:.2f}\n"

    def send_to_serial(self, message: str):
        if self.serial_port is None:
            self.get_logger().warning(f"Serial unavailable, skipped command: {message.strip()}")
            return

        try:
            self.serial_port.write(message.encode())
            self.get_logger().info(f"Sent: {message.strip()}")

            response = self.serial_port.readline().decode(errors='ignore').strip()
            if response:
                self.get_logger().info(f"Arduino says: {response}")
        except Exception as exc:
            self.get_logger().error(f"Serial write failed: {exc}")


def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryToSerial()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
