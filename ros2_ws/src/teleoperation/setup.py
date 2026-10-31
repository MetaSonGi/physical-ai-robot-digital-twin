import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'teleoperation'

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
    description='Leader-follower teleoperation relay for OpenMANIPULATOR-X.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'leader_follower = teleoperation.leader_follower_node:main',
        ],
    },
)
