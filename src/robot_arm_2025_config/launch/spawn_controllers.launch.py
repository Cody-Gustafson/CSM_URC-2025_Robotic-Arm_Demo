#from moveit_configs_utils import MoveItConfigsBuilder
#from moveit_configs_utils.launches import generate_spawn_controllers_launch


#def generate_launch_description():
#    moveit_config = MoveItConfigsBuilder("robot_arm_2025", package_name="robot_arm_2025_config").to_moveit_configs()
#    return generate_spawn_controllers_launch(moveit_config)


from launch import LaunchDescription

def generate_launch_description():
    return LaunchDescription()