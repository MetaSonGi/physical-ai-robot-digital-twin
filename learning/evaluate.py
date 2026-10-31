"""Offline evaluation on held-out demonstrations.

    python -m learning.evaluate --ckpt runs/bc_default/best.pt

Metrics
  - open-loop MAE / RMSE : one-step prediction error given ground-truth history
  - closed-loop success  : the policy drives a simulated first-order follower
                           (same dynamics as generate_synthetic.py) from the demo start.
                           Success = reaches the pick pose with gripper closed, then
                           reaches the place pose with gripper open (|err| < tol).
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import torch

from learning.dataset import load_episode
from learning.models import BCPolicy


def rollout(model: BCPolicy, obs0: np.ndarray, context: np.ndarray | None, steps: int,
            gain: float = 0.5) -> np.ndarray:
    H = model.history
    q = obs0.copy()
    full = lambda q: q if context is None else np.r_[q, context]  # noqa: E731
    hist = [full(q) for _ in range(H)]
    traj = [q.copy()]
    for _ in range(steps):
        x = torch.from_numpy(np.stack(hist[-H:])[None].astype(np.float32))
        cmd = model.predict(x)[0].numpy()
        q = q + gain * (cmd - q)
        hist.append(full(q))
        traj.append(q.copy())
    return np.stack(traj)


def task_success(traj: np.ndarray, pick: np.ndarray, place: np.ndarray, tol: float) -> bool:
    picked_at = None
    for i, q in enumerate(traj):
        if picked_at is None and np.abs(q[:4] - pick).max() < tol and q[4] < 0:
            picked_at = i
        elif picked_at is not None and np.abs(q[:4] - place).max() < tol and q[4] > 0:
            return True
    return False


def evaluate(ckpt: str, tol: float = 0.08) -> dict:
    model = BCPolicy.load(ckpt)
    meta = torch.load(ckpt, map_location="cpu", weights_only=False)
    H = model.history
    abs_err, successes = [], []
    for p in meta["val_episodes"]:
        ep = np.load(p)
        pobs, act = load_episode(p)
        pad = np.concatenate([np.repeat(pobs[:1], H - 1, 0), pobs])
        windows = np.stack([pad[t:t + H] for t in range(len(pobs) - 1)])
        pred = model.predict(torch.from_numpy(windows)).numpy()
        abs_err.append(np.abs(pred - act[1:]))
        if "context" in ep.files:
            ctx = ep["context"].astype(np.float32)
            traj = rollout(model, ep["obs"][0].astype(np.float32), ctx, int(len(pobs) * 1.5))
            successes.append(task_success(traj, ctx[:4], ctx[4:8], tol))
    e = np.concatenate(abs_err)
    return {
        "episodes": len(meta["val_episodes"]),
        "open_loop_mae_rad": round(float(e.mean()), 5),
        "open_loop_rmse_rad": round(float(np.sqrt((e ** 2).mean())), 5),
        "per_joint_mae_rad": e.mean(0).round(5).tolist(),
        "closed_loop_success_rate": float(np.mean(successes)) if successes else None,
        "success_tol_rad": tol,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="runs/bc_default/best.pt")
    ap.add_argument("--tol", type=float, default=0.08)
    args = ap.parse_args()
    print(json.dumps(evaluate(args.ckpt, args.tol), indent=2))


if __name__ == "__main__":
    main()
