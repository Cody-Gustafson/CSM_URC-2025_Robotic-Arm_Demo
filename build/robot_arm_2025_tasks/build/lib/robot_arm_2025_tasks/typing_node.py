import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from tf_transformations import quaternion_multiply, quaternion_from_euler
import math
import time

from moveit_msgs.action import MoveGroup
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import MotionPlanRequest, Constraints, JointConstraint

from sensor_msgs.msg import JointState

from robot_arm_2025_tasks.keyboard_geometry import KeyboardGeometry
from robot_arm_2025_tasks.key_map import KeyMap


class TypingNode(Node):

    def __init__(self):
        super().__init__('typing_node')

        self.group_name = "arm"
        self.ee_link = "ToolEnd"

        # MoveGroup action
        self.move_action = ActionClient(self, MoveGroup, '/move_action')
        self.get_logger().info("Waiting for MoveGroup...")
        self.move_action.wait_for_server()
        self.get_logger().info("MoveGroup ready.")

        # IK service
        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')
        self.get_logger().info("Waiting for IK service...")
        self.ik_client.wait_for_service()
        self.get_logger().info("IK service ready.")

        # Joint state subscription
        self.current_joint_state = None
        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )

        self.keyboard = KeyboardGeometry()
        self.keymap = KeyMap()

    # =====================================================
    # Joint State Callback
    # =====================================================

    def joint_state_callback(self, msg):
        # print("Joint state received!")
        self.current_joint_state = msg

    # =====================================================
    # Compute IK (seeded from current state automatically)
    # =====================================================

    def compute_ik(self, pose):

        # print (pose)

        if self.current_joint_state is None:
            self.get_logger().error("No joint state received yet.")
            return None

        # Extract original quaternion
        q_orig = [
            pose.pose.orientation.x,
            pose.pose.orientation.y,
            pose.pose.orientation.z,
            pose.pose.orientation.w
        ]

        # Sweep rotation about local Z
        for angle_deg in range(-180, 181, 5):

            angle_rad = math.radians(angle_deg)

            # Rotation about local Z axis
            q_rot = quaternion_from_euler(0, 0, angle_rad)

            # Multiply: original * rotation
            q_new = quaternion_multiply(q_orig, q_rot)

            # Build modified pose
            test_pose = pose
            test_pose.pose.orientation.x = q_new[0]
            test_pose.pose.orientation.y = q_new[1]
            test_pose.pose.orientation.z = q_new[2]
            test_pose.pose.orientation.w = q_new[3]

            request = GetPositionIK.Request()
            request.ik_request.group_name = self.group_name
            request.ik_request.pose_stamped = test_pose
            request.ik_request.robot_state.joint_state = self.current_joint_state
            request.ik_request.avoid_collisions = False

            future = self.ik_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)

            response = future.result()

            if response.error_code.val == 1:
                self.get_logger().info(
                    f"IK success at Z rotation {angle_deg} degrees"
                )
                return response.solution.joint_state

        self.get_logger().error("IK sweep failed: no valid solution found.")
        return None

    # =====================================================
    # Build Joint Goal
    # =====================================================

    def build_joint_goal(self, joint_state):

        goal = MoveGroup.Goal()
        request = MotionPlanRequest()

        request.group_name = self.group_name
        request.start_state.is_diff = True
        request.num_planning_attempts = 5
        request.allowed_planning_time = 3.0

        constraints = Constraints()

        for name, position in zip(joint_state.name, joint_state.position):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = position
            jc.tolerance_above = 0.001
            jc.tolerance_below = 0.001
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        request.goal_constraints.append(constraints)

        goal.request = request
        goal.planning_options.plan_only = True

        return goal

    # =====================================================
    # Execute
    # =====================================================

    def execute(self, goal):
    
        future = self.move_action.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected.")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        if result.error_code.val != 1:
            self.get_logger().error(
                f"Planning failed: {result.error_code.val}"
            )
            return False

        self.get_logger().info("Plan successful.")
        return True

    # =====================================================
    # Move To Pose via IK → Joint Goal
    # =====================================================

    def move_to_pose(self, pose):

        joint_solution = self.compute_ik(pose)
        if joint_solution is None:
            return False

        goal = self.build_joint_goal(joint_solution)
        return self.execute(goal)

    # =====================================================
    # Press Key
    # =====================================================

    def press_key(self, row, col):

        key_pose = self.keyboard.get_key_pose(row, col)

        approach = self.keyboard.offset_along_normal(key_pose, -0.03)
        press = self.keyboard.offset_along_normal(key_pose, -0.005)
        retreat = approach

        for pose in [approach, press, retreat]:
            if not self.move_to_pose(pose):
                return False

            time.sleep(1.0)

        return True

    # =====================================================
    # Type String
    # =====================================================

    def type_string(self, text):

        for char in text:
            key = self.keymap.get_key(char)

            if key is None:
                self.get_logger().warn(f"Unknown key: {char}")
                continue

            row, col = key
            self.get_logger().info(f"Pressing {char}")

            if not self.press_key(row, col):
                self.get_logger().error(f"Failed pressing {char}")
                break


# =========================================================

def main(args=None):

    rclpy.init(args=args)
    node = TypingNode()

    # Give time for joint states to arrive
    while rclpy.ok() and node.current_joint_state is None:
        rclpy.spin_once(node)

    node.get_logger().info("Joint state received. Starting motion.")

    # First ensure you're already in keyboard-ready pose
    print("Key 1")
    node.press_key(1, 5)
    print("Key 2")
    node.press_key(2, 5)
    print("Key 3")
    node.press_key(1, 4)

    rclpy.shutdown()


if __name__ == '__main__':
    main()