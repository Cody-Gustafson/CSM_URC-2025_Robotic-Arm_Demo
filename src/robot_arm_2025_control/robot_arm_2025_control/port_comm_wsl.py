import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from moveit_msgs.msg import DisplayTrajectory

import zmq
import struct
import subprocess

class PortCommWSL(Node):
    def __init__(self):
        super().__init__('port_comm_wsl')

        # --- 1. ZMQ SETUP ---
        host_ip = self.get_windows_ip()
        self.get_logger().info(f"Connecting to Windows IP: {host_ip}")
        
        self.zmq_context = zmq.Context()
        
        # Command Sender (PUSH)
        self.command_sender = self.zmq_context.socket(zmq.PUSH)
        self.command_sender.connect(f"tcp://{host_ip}:5000")
        
        # Feedback Receiver (SUB)
        self.feedback_receiver = self.zmq_context.socket(zmq.SUB)
        self.feedback_receiver.connect(f"tcp://{host_ip}:5005")
        self.feedback_receiver.setsockopt_string(zmq.SUBSCRIBE, "")

        # --- 2. ROS SETUP ---
        # NOTE: Change these names to exactly match the joint names in your URDF!
        self.joint_names = ['J1', 'J2', 'J3', 'J4', 'J5']

        # Publisher to send Windows feedback back into ROS
        self.joint_pub = self.create_publisher(JointState, 'joint_states', 10)
        
        # Timer to constantly poll ZMQ for new feedback (100Hz)
        self.timer = self.create_timer(0.01, self.poll_zmq_feedback)

        # Subscriber to intercept MoveIt's display trajectories
        self.traj_sub = self.create_subscription(
            DisplayTrajectory, 
            'display_planned_path', 
            self.trajectory_callback, 
            10
        )

        self.get_logger().info("ZMQ-ROS2 Bridge is up and running.")

    def get_windows_ip(self):
        cmd = "ip route show | grep default | awk '{print $3}'"
        return subprocess.check_output(cmd, shell=True).decode().strip()

    def trajectory_callback(self, msg):
        """Triggered whenever MoveIt publishes a new display trajectory."""
        
        # Safety check: ensure there is actually a trajectory in the message
        if not msg.trajectory or not msg.trajectory[0].joint_trajectory.points:
            return

        # MoveIt can send multiple trajectories in one message
        for traj in msg.trajectory:
            if traj.joint_trajectory.points:
                # Grab the very last point of the plan
                target_point = traj.joint_trajectory.points[-1]
                positions = target_point.positions
                
                if len(positions) >= 5:
                    command_tuple = tuple(positions[:5])
                    cmd_bytes = struct.pack('<5f', *command_tuple)
                    self.command_sender.send(cmd_bytes)
                    self.get_logger().info(f"PLAN RECEIVED: Sent target {command_tuple} to Windows")

    def poll_zmq_feedback(self):
        """Triggered 100 times a second by the ROS timer to check for feedback."""
        try:
            # Non-blocking receive
            feedback_bytes = self.feedback_receiver.recv(flags=zmq.NOBLOCK)
            
            # Unpack the 15 floats (5 Pos, 5 Vel, 5 Acc)
            feedback_data = struct.unpack('<15f', feedback_bytes)

            # Print input from Windows
            self.get_logger().info(
                f"\n--- FULL FEEDBACK RECEIVED ---\n"
                f"POS: {feedback_data[0:5]}\n"
                f"VEL: {feedback_data[5:10]}\n"
                f"ACC: {feedback_data[10:15]}\n"
                f"------------------------------",
                throttle_duration_sec=1.0
            )
            
            # Construct the ROS JointState message
            js_msg = JointState()
            js_msg.header.stamp = self.get_clock().now().to_msg()
            js_msg.name = self.joint_names
            
            js_msg.position = list(feedback_data[0:5])
            js_msg.velocity = list(feedback_data[5:10])
            
            # Note: The standard ROS JointState message has 'effort', not 'acceleration'.
            # We will map your acceleration floats into the effort array so MoveIt can still log it.
            js_msg.effort = list(feedback_data[10:15])

            # Publish to ROS
            self.joint_pub.publish(js_msg)

        except zmq.Again:
            pass # No new feedback from Windows this tick
        except Exception as e:
            self.get_logger().error(f"Error parsing ZMQ data: {e}")

    def destroy_node(self):
        """Cleanup ZMQ sockets when ROS shuts down."""
        self.command_sender.close()
        self.feedback_receiver.close()
        self.zmq_context.term()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    bridge_node = PortCommWSL()
    
    try:
        rclpy.spin(bridge_node)
    except KeyboardInterrupt:
        pass
    finally:
        bridge_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()