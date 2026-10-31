import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'policy_inference'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hyogi son',
    maintainer_email='sonhyogi0078@gmail.com',
    description='Runs a trained Behavior Cloning policy as a ROS 2 node.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'policy_node = policy_inference.policy_node:main',
        ],
    },
)
