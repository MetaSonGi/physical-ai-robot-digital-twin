import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'data_recorder'

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
    description='Records synchronized leader/follower demonstrations to .npz episodes.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'recorder = data_recorder.recorder_node:main',
        ],
    },
)
