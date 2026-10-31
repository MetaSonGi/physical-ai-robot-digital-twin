# Datasets

Episodes are not committed (see `.gitignore`). Generate or record them:

```bash
python3 -m learning.generate_synthetic --out datasets/synthetic_pick_place --episodes 200   # no hardware
ros2 launch robot_bringup demo.launch.py mode:=teleop out_dir:=datasets/pick_place          # real OMX
```

Format: one `episode_XXXX.npz` per demonstration — see [`docs/data-format.md`](../docs/data-format.md).
