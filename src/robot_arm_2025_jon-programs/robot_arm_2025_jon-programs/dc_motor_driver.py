import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

import ctypes


class DCMotorDriver(Node):

    def __init__(self):

        super().__init__('dc_motor_driver')

        self.lib = ctypes.CDLL("/home/urc/sparkcan/build/libspark_bridge.so")

        self.motor_ids = {
            "joint2": 1,
            "joint3": 2
        }

        for mid in self.motor_ids.values():
            self.lib.init_motor(b"can1", mid)

        self.subscription = self.create_subscription(
            JointState,
            '/joint_commands',
            self.command_callback,
            10
        )

        self.get_logger().info("DC motor driver ready")


    def command_callback(self, msg):

        for name, pos in zip(msg.name, msg.position):

            if name in self.motor_ids:

                motor_id = self.motor_ids[name]

                power = pos  # example conversion

                self.lib.set_power(
                    motor_id,
                    ctypes.c_float(power)
                )


def main():

    rclpy.init()

    node = DCMotorDriver()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()