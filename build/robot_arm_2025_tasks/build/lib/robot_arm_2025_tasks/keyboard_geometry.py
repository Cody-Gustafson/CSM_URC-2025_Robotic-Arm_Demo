import numpy as np
from geometry_msgs.msg import PoseStamped


class KeyboardGeometry:

    def __init__(self):

        # =====================================================
        # Keyboard Origin (WORKING POSE FROM RVIZ)
        # This should be a reachable "home key" position
        # =====================================================

        self.origin_position = np.array([
            0.022313999012112617,
            -0.4279371201992035,
            0.304404079914093
        ])

        # Tool orientation that worked at origin
        self.origin_quaternion = [
            0.999993622303009,
            -1.2587050150614232e-05,
            -7.029645416878338e-07,
            -0.003572165733203292
        ]

        # =====================================================
        # Explicit Keyboard Frame Definition (WORLD FRAME)
        # =====================================================

        # Columns: left/right
        self.col_axis = np.array([1.0, 0.0, 0.0])   # World X

        # Rows: up/down
        self.row_axis = np.array([0.0, 0.0, 1.0])   # World Z

        # Press direction (normal to keyboard plane)
        # Robot forward is -Y, so keyboard faces robot → normal = +Y
        self.normal_axis = np.array([0.0, -1.0, 0.0])

        # =====================================================
        # Layout Parameters
        # =====================================================

        self.key_spacing = 0.018  # 18 mm
        self.home_row = 1
        self.home_col = 5

    # =====================================================
    # Get Pose of a Key
    # =====================================================

    def get_key_pose(self, row, col):

        # Column offset (left/right)
        u = (col - self.home_col) * self.key_spacing

        # Row offset (up/down)
        v = (self.home_row - row) * self.key_spacing

        position = (
            self.origin_position
            + u * self.col_axis
            + v * self.row_axis
        )

        pose = PoseStamped()
        pose.header.frame_id = "world"

        pose.pose.position.x = position[0]
        pose.pose.position.y = position[1]
        pose.pose.position.z = position[2]

        pose.pose.orientation.x = self.origin_quaternion[0]
        pose.pose.orientation.y = self.origin_quaternion[1]
        pose.pose.orientation.z = self.origin_quaternion[2]
        pose.pose.orientation.w = self.origin_quaternion[3]

        return pose

    # =====================================================
    # Offset Along Keyboard Normal (Approach / Press)
    # =====================================================

    def offset_along_normal(self, pose, distance):

        position = np.array([
            pose.pose.position.x,
            pose.pose.position.y,
            pose.pose.position.z
        ])

        new_position = position + distance * self.normal_axis

        new_pose = PoseStamped()
        new_pose.header.frame_id = "world"

        new_pose.pose.position.x = new_position[0]
        new_pose.pose.position.y = new_position[1]
        new_pose.pose.position.z = new_position[2]

        new_pose.pose.orientation = pose.pose.orientation

        return new_pose