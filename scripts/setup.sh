#!/usr/bin/env bash
# Ubuntu 24.04 + ROS 2 Jazzy. Installs Python deps, the Unity TCP endpoint, and builds the workspace.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /opt/ros/jazzy/setup.bash

pip install -r "$ROOT/requirements.txt"

cd "$ROOT/ros2_ws/src"
[ -d ROS-TCP-Endpoint ] || git clone -b main-ros2 https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git
cd "$ROOT/ros2_ws"
rosdep install --from-paths src --ignore-src -y || true
colcon build --symlink-install
echo "done. run: source ros2_ws/install/setup.bash"
