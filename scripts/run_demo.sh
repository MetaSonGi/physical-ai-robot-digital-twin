#!/usr/bin/env bash
# End-to-end demo without hardware:
#   synthetic demos -> validate -> train -> evaluate -> ROS 2 sim (policy + safety + sim follower)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"

python3 -m learning.generate_synthetic --episodes 200
python3 -m learning.validate_dataset datasets/synthetic_pick_place
python3 -m learning.train --config learning/configs/bc_default.json
python3 -m learning.evaluate --ckpt runs/bc_default/best.pt

if [ "${1:-}" = "--ros" ]; then
  source /opt/ros/jazzy/setup.bash
  source ros2_ws/install/setup.bash
  EP=$(ls datasets/synthetic_pick_place/episode_*.npz | tail -1)
  ros2 launch robot_bringup demo.launch.py mode:=sim checkpoint:="$ROOT/runs/bc_default/best.pt" \
       episode:="$ROOT/$EP" unity:="${UNITY:-false}"
fi
