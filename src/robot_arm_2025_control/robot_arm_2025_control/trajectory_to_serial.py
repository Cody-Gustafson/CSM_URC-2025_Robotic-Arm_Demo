#!/usr/bin/env python3

import serial
import time
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
from sensor_msgs.msg import JointState
import math


class TrajectoryToSerial(Node):

    def __init__(self):
        super().__init__('trajectory_to_serial')

        # ---- Serial Setup ----
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
            time.sleep(2)
            self.get_logger().info("Serial connection established.")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            self.serial_port = None

        # ---- ROS Subscription ----
        self.subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.trajectory_callback,
            10
        )

        self.get_logger().info("Trajectory listener started.")

        # ---- Joint State Publisher ----
        self.joint_state_pub = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )

        self.joint_names = [
            'J1',
            'J2',
            'J3',
            'J4',
            'J5'
        ]

        # Track current joint positions internally (radians!)
        self.current_joint_positions = [0.0, 0.0, 0.0, 0.0, 0.0]

        # ---- Repeat Publisher ----
        self.joint_state_timer = self.create_timer(
            0.033,  # 30 Hz
            self.publish_joint_state
        )

    # =====================================================

    def publish_joint_state(self):

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = self.current_joint_positions

        self.joint_state_pub.publish(msg)

    # =====================================================

    def trajectory_callback(self, msg):

        if not msg.trajectory:
            return

        traj = msg.trajectory[0].joint_trajectory

        if not traj.points:
            return

        # Get final waypoint (in radians)
        final_point = traj.points[-1]
        joint_names = traj.joint_names
        positions = final_point.positions

        # Update internal joint state BEFORE motor conversion
        self.current_joint_positions = list(positions)
        self.publish_joint_state()

        joint_dict = dict(zip(joint_names, positions))

        # Extract MoveIt joints (radians)
        J1 = joint_dict.get('J1', 0.0)
        J2 = joint_dict.get('J2', 0.0)
        J3 = joint_dict.get('J3', 0.0)
        J4 = joint_dict.get('J4', 0.0)
        J5 = joint_dict.get('J5', 0.0)

        # ---- Parallelogram compensation ----
        motor_J1 = J1
        motor_J2 = J2
        motor_J3 = -(J3 + J2)
        motor_J4 = J4
        motor_J5 = J5

        # ---- Convert to degrees ----
        rad_to_deg = 180.0 / math.pi

        motor_J1 = motor_J1 * rad_to_deg + 90
        motor_J2 = motor_J2 * rad_to_deg + 90
        motor_J3 = motor_J3 * rad_to_deg + 90
        motor_J4 = motor_J4 * rad_to_deg + 90
        motor_J5 = motor_J5 * rad_to_deg + 90

        # ---- Clamp servo range ----
        def clamp(val, min_val=0, max_val=180):
            return max(min(val, max_val), min_val)

        motor_J1 = clamp(motor_J1)
        motor_J2 = clamp(motor_J2)
        motor_J3 = clamp(motor_J3)
        motor_J4 = clamp(motor_J4)
        motor_J5 = clamp(motor_J5)

        # ---- Format CSV Message ----
        message = f"{motor_J1:.2f},{motor_J2:.2f},{motor_J3:.2f},{motor_J4:.2f},{motor_J5:.2f}\n"

        # ---- Send Over Serial ----
        if self.serial_port is not None:
            try:
                self.serial_port.write(message.encode())
                self.get_logger().info(f"Sent: {message.strip()}")

                while True:
                    response = self.serial_port.readline().decode(errors='ignore').strip()
                    if response:
                        print("Arduino says:", response)
                    if response in ["OK", "PARSE_FAIL"]:
                        break
            except Exception as e:
                self.get_logger().error(f"Serial write failed: {e}")


# =====================================================

def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryToSerial()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()