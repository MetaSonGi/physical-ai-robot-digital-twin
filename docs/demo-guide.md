# Demo guide

## A. No hardware (5 min)
```bash
pip install -r requirements.txt
./scripts/run_demo.sh            # synthetic data → train → evaluate
./scripts/run_demo.sh --ros      # + ROS 2 sim loop (after scripts/setup.sh)
UNITY=true ./scripts/run_demo.sh --ros   # + Unity twin
```

## B. Real robot
```bash
# 1. collect demonstrations
ros2 launch robot_bringup demo.launch.py mode:=teleop out_dir:=$PWD/datasets/pick_place unity:=true
ros2 service call /recorder/start std_srvs/srv/Trigger   # move leader arm
ros2 service call /recorder/stop  std_srvs/srv/Trigger   # or /recorder/discard

# 2. train
python3 -m learning.validate_dataset datasets/pick_place
python3 -m learning.train --data_dir datasets/pick_place --out_dir runs/pick_place
python3 -m learning.evaluate --ckpt runs/pick_place/best.pt

# 3. deploy (driver running separately)
ros2 launch robot_bringup demo.launch.py mode:=hardware checkpoint:=$PWD/runs/pick_place/best.pt unity:=true
```

## What to record for the portfolio
- Side-by-side video: real arm | Unity twin | HUD
- `runs/*/loss_history.csv` plot, `evaluate` JSON
- Success / failure clips with a one-line cause for each failure
