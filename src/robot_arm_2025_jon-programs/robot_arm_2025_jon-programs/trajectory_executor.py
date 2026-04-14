import rclpy
from rclpy.node import Node
import serial
import time
import numpy as np
from collections import deque # More efficient for popping from the front

from moveit_msgs.msg import DisplayTrajectory
from sensor_msgs.msg import JointState

class TrajectoryExecutor(Node):

    def __init__(self):
        super().__init__('trajectory_executor')

        # 1. Serial Initialization
        try:
            # Adjust the port name as needed for your robot's OS
            self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.01)
            self.get_logger().info("Serial port opened successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial port: {e}")

        # 2. Data Structures
        self.point_queue = deque()  # Stores interpolated joint positions
        self.rate_hz = 50.0

        # 3. ROS Communications
        self.subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.trajectory_callback,
            10)

        self.publisher = self.create_publisher(
            JointState,
            '/joint_commands',
            10)

        # 4. Timers (The "Heartbeat" of the system)
        # Execution Timer: Picks points from the queue and sends them to hardware
        self.execution_timer = self.create_timer(1.0/self.rate_hz, self.execution_loop)
        
        # Feedback Timer: Sends robot status back to Windows
        self.feedback_timer = self.create_timer(0.02, self.send_feedback_to_windows)

        self.get_logger().info("Trajectory Executor Refactored: Ready")

    def trajectory_callback(self, msg):
        """Processes a new path and breaks it into a high-frequency queue."""
        self.get_logger().info("Received new trajectory. Interpolating...")
        
        traj = msg.trajectory[0].joint_trajectory
        points = traj.points
        
        # We build a temporary list to avoid clearing the active queue mid-motion
        temp_queue = []

        for i in range(len(points)-1):
            p0 = points[i]
            p1 = points[i+1]

            t0 = p0.time_from_start.sec + p0.time_from_start.nanosec * 1e-9
            t1 = p1.time_from_start.sec + p1.time_from_start.nanosec * 1e-9

            duration = t1 - t0
            steps = int(duration * self.rate_hz)

            if steps > 0:
                start = np.array(p0.positions)
                end = np.array(p1.positions)

                # Linear interpolation between waypoints
                for s in range(steps):
                    alpha = s / steps
                    pos = start * (1 - alpha) + end * alpha
                    temp_queue.append(pos.tolist())

        # Thread-safe update: Clear old motion and start new motion
        self.point_queue.clear()
        self.point_queue.extend(temp_queue)
        self.get_logger().info(f"Queue loaded with {len(temp_queue)} points.")

    def execution_loop(self):
        """Timer-based loop that handles serial I/O and joint publishing."""
        
        # A. SEND COMMANDS: If we have points in the queue, execute the next one
        if self.point_queue:
            next_pos = self.point_queue.popleft()
            
            # Publish to ROS
            msg_out = JointState()
            msg_out.position = next_pos
            self.publisher.publish(msg_out)

            # Send to Windows/Serial Bus
            # Format: "pos1,pos2,pos3,pos4,pos5\n"
            cmd_str = ",".join(f"{val:.4f}" for val in next_pos) + "\n"
            self.ser.write(cmd_str.encode('utf-8'))

        # B. RECEIVE COMMANDS: Check if Windows sent an override/direct command
        if self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    # If Windows sends data, it overrides the current trajectory
                    override_pos = list(map(float, line.split(',')))
                    self.point_queue.clear() # Stop current trajectory
                    
                    msg_out = JointState()
                    msg_out.position = override_pos
                    self.publisher.publish(msg_out)
            except Exception as e:
                self.get_logger().warn(f"Serial Parse Error: {e}")

    def send_feedback_to_windows(self):
        """Sends 15-float feedback packet to the base station."""
        # Replace these placeholders with your actual sensor readings!
        feedback = [1.0] * 15 
        fb_str = ",".join(f"{val:.4f}" for val in feedback) + "\n"
        try:
            self.ser.write(fb_str.encode('utf-8'))
        except Exception as e:
            self.get_logger().error(f"Serial Write Error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.ser.is_open:
            node.ser.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()