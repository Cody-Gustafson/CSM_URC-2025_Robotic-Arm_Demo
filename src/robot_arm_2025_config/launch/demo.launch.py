from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_demo_launch


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder(
        "robot_arm_2025", package_name="robot_arm_2025_config"
    ).to_moveit_configs()

    demo_launch = generate_demo_launch(moveit_config)
    demo_launch.add_action(
        Node(
            package="robot_arm_2025_control",
            executable="trajectory_to_serial",
            output="screen",
        )
    )

    return LaunchDescription(demo_launch.entities)
