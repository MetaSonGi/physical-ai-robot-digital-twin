import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'robot_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hyogi son',
    maintainer_email='sonhyogi0078@gmail.com',
    description='Launch files, parameters and simulation/replay helpers (sim_follower, episode_replayer).',
    license='MIT',
    entry_points={
        'console_scripts': [
            'sim_follower = robot_bringup.sim_follower:main',
            'episode_replayer = robot_bringup.episode_replayer:main',
        ],
    },
)
