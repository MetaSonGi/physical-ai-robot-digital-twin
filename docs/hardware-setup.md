# Hardware setup (OpenMANIPULATOR-X)

1. Ubuntu 24.04 + ROS 2 Jazzy, U2D2 connected to the follower (and leader) arm.
2. Install the ROBOTIS driver (`open_manipulator` repo, Jazzy branch) and confirm
   `ros2 topic echo /joint_states` shows `joint1..joint4` and the gripper.
3. `./scripts/setup.sh` — builds this workspace and the Unity TCP endpoint.
4. Edit `robot_bringup/config/robot.yaml` to match your driver's topic/joint names
   (`ros2 topic list`, `ros2 control list_controllers`).
5. Leader arm: torque **off** so it can be moved by hand; it must publish `/leader/joint_states`.
   If your driver ships its own leader/follower launch, use it and only run `data_recorder`.

## Safety checklist before autonomous runs

- [ ] Clear workspace, arm within reach of a physical stop
- [ ] `ros2 topic pub /safety/estop std_msgs/Bool "{data: true}"` holds the arm
- [ ] Joint limits in `safety_filter.py` match your URDF
- [ ] First runs at reduced `max_vel`
