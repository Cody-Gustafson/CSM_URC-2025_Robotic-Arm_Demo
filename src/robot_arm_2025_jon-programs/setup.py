from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'robot_arm_2025_jon-programs'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cody',
    maintainer_email='cdgustafson.cg@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            #'servo_control = robot_arm_2025_jon-programs.servo_control:main'
            #'neo_control = robot_arm_2025_jon-programs.neo_control:main'
        ],
    },
)
