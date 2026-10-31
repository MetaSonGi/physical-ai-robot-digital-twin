# Unity Digital Twin

Tested target: Unity 2022.3 LTS. `Packages/manifest.json` pulls ROS-TCP-Connector and URDF-Importer.

1. Open `unity/PhysicalAIRobotTwin` in Unity Hub (it will generate `ProjectSettings/`).
2. **Robotics → ROS Settings**: protocol `ROS2`, IP of the ROS machine, port `10000`.
3. Import the OpenMANIPULATOR-X URDF (from the `open_manipulator` description package) via
   *Assets → Import Robot from URDF*. Set the root `ArticulationBody` to **Immovable**.
4. Create an empty `TwinController`, add `RobotTwinController`, and bind
   `joint1..joint4` + `gripper_left_joint` (check *prismatic*) to their links.
5. Add `TelemetryHUD` (assign the controller) and `EStopButton`.
6. ROS side: `ros2 launch robot_bringup demo.launch.py mode:=replay episode:=<npz> unity:=true`.

| Script | Role |
|---|---|
| `RobotTwinController.cs` | `/joint_states` → ArticulationBody drives; echoes `/unity/joint_states` for sync/latency |
| `TelemetryHUD.cs` | Joint angles, sync error, round-trip latency, policy latency, safety status |
| `EStopButton.cs` | Publishes `/safety/estop` (Space) |
