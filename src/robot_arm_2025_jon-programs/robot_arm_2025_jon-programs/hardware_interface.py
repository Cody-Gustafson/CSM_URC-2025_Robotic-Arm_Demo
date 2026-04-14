import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from moveit_msgs.msg import DisplayTrajectory

import serial
import ctypes
import socket
import struct
import time
import os


class ArmHardwareInterface(Node):

    def __init__(self):

        super().__init__('arm_hardware_interface')

        # -------------------------
        # Servo configuration
        # -------------------------

        self.servo_joints = ["joint1","joint4","joint5"]
        self.ser = serial.Serial('/dev/ttyUSB0',115200)

        # -------------------------
        # CAN configuration
        # -------------------------

        os.system("sudo ip link set can1 up type can bitrate 1000000")

        self.lib = ctypes.CDLL("/home/urc/sparkcan/build/libspark_bridge.so")

        self.dc_motor_map = {
            "joint2":1,
            "joint3":2
        }

        for mid in self.dc_motor_map.values():
            self.lib.init_motor(b"can1", mid)

        # CAN telemetry socket

        self.can_sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.can_sock.bind(('can1',))
        self.can_sock.setblocking(False)

        # -------------------------
        # ROS interfaces
        # -------------------------

        self.subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.trajectory_callback,
            10
        )

        self.joint_state_pub = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )

        # state storage

        self.joint_positions = {
            "joint1":0.0,
            "joint2":0.0,
            "joint3":0.0,
            "joint4":0.0,
            "joint5":0.0
        }

        # timers

        self.create_timer(0.02,self.telemetry_loop)

        self.get_logger().info("Hardware interface ready")


    # ---------------------------------------------------
    # Trajectory execution
    # ---------------------------------------------------

    def trajectory_callback(self,msg):

        traj = msg.trajectory[0].joint_trajectory

        names = traj.joint_names
        points = traj.points

        for p in points:

            for name,pos in zip(names,p.positions):

                self.joint_positions[name] = pos

            self.send_servo_commands()
            self.send_dc_commands()

            time.sleep(0.02)


    # ---------------------------------------------------
    # Servo control
    # ---------------------------------------------------

    def send_servo_commands(self):

        s = []

        for j in self.servo_joints:

            angle = int(self.joint_positions[j]*180/3.14159)

            s.append(str(angle))

        msg = "<" + ",".join(s) + ">\n"

        self.ser.write(msg.encode())


    # ---------------------------------------------------
    # DC motor control
    # ---------------------------------------------------

    def send_dc_commands(self):

        for joint,motor_id in self.dc_motor_map.items():

            pos = self.joint_positions[joint]

            power = pos  # placeholder conversion

            self.lib.set_power(
                motor_id,
                ctypes.c_float(power)
            )


    # ---------------------------------------------------
    # Encoder feedback
    # ---------------------------------------------------

    def telemetry_loop(self):

        try:

            while True:

                frame = self.can_sock.recv(16)

                can_id, dlc, data = struct.unpack("<IB3x8s",frame)

                # decode telemetry here

        except BlockingIOError:
            pass

        msg = JointState()

        msg.name = list(self.joint_positions.keys())
        msg.position = list(self.joint_positions.values())

        self.joint_state_pub.publish(msg)



def main():

    rclpy.init()

    node = ArmHardwareInterface()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()