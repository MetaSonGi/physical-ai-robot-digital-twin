# Demonstration data format

| key | shape | dtype | meaning |
|---|---|---|---|
| `t` | (T,) | float64 | seconds since episode start |
| `obs` | (T, 5) | float32 | follower `joint1..joint4` [rad] + `gripper_left_joint` [m] |
| `action` | (T, 5) | float32 | leader command at the same tick (same units, gripper scaled) |
| `context` | (C,) | float32 | *optional* task context — object/goal pose from perception |
| `success` | () | bool | operator label; failed demos are filtered out |

Policy input per frame = `concat(obs[t], context)`; the model sees the last `history` frames.
Training target (`action_mode: delta`) = `action[t+1] - obs[t]`.

## Validation rules (`learning/validate_dataset.py`)

- at least 20 frames, equal lengths, no NaN/Inf
- no timestamp gap > 0.2 s (dropped messages)
- |joint| ≤ 3.2 rad
- `success == True`

Train/val are split **by episode**, never by frame, to avoid leakage.
