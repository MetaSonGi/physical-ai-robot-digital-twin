import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'unity_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hyogi son',
    maintainer_email='sonhyogi0078@gmail.com',
    description='ROS-TCP endpoint launch and Unity-facing telemetry (sync latency).',
    license='MIT',
    entry_points={
        'console_scripts': [
            'twin_telemetry = unity_bridge.twin_telemetry_node:main',
        ],
    },
)
