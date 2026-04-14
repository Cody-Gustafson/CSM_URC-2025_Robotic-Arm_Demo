import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState

import serial

class ServoDriver(Node):

    def __init__(self):

        super().__init__('servo_driver')

        self.serial = serial.Serial('/dev/ttyUSB0', 115200)

        self.subscription = self.create_subscription(
            JointState,
            '/joint_commands',
            self.command_callback,
            10)

    def command_callback(self, msg):

        cmd = ""

        for name, pos in zip(msg.name, msg.position):

            if name in ["joint1","joint2","joint3"]:

                angle = int(pos * 180 / 3.14159)

                cmd += f"{name}:{angle} "

        cmd += "\n"

        self.serial.write(cmd.encode())


def main(args=None):

    rclpy.init(args=args)

    node = ServoDriver()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()