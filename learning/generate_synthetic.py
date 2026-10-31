"""Generate synthetic pick&place demonstrations so the pipeline runs without hardware.

    python -m learning.generate_synthetic --out datasets/synthetic_pick_place --episodes 40
"""
from __future__ import annotations

import argparse
import os

import numpy as np

HOME = np.array([0.0, -1.0, 0.3, 0.7, 0.01])


def make_episode(rng: np.random.Generator, hz: float = 20.0) -> dict:
    pick = np.array([rng.uniform(-0.6, 0.6), rng.uniform(0.2, 0.6), rng.uniform(-0.2, 0.3), rng.uniform(0.6, 1.2)])
    place = np.array([rng.uniform(-0.6, 0.6), rng.uniform(0.2, 0.6), rng.uniform(-0.2, 0.3), rng.uniform(0.6, 1.2)])
    above = lambda q: q + np.array([0, -0.35, 0.1, 0])  # noqa: E731
    open_g, closed_g = 0.01, -0.01
    waypoints = [
        np.r_[HOME[:4], open_g], np.r_[above(pick), open_g], np.r_[pick, open_g], np.r_[pick, closed_g],
        np.r_[above(pick), closed_g], np.r_[above(place), closed_g], np.r_[place, closed_g],
        np.r_[place, open_g], np.r_[above(place), open_g], np.r_[HOME[:4], open_g],
    ]
    seg_len = rng.integers(15, 30, size=len(waypoints) - 1)
    cmd = []
    for a, b, n in zip(waypoints[:-1], waypoints[1:], seg_len):
        s = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n, endpoint=False))  # smooth min-jerk-ish
        cmd.append(a + (b - a) * s[:, None])
    cmd = np.concatenate(cmd).astype(np.float32)
    cmd += rng.normal(0, 0.005, cmd.shape).astype(np.float32)  # operator hand tremor
    # follower lags the leader by a first-order response
    obs = np.zeros_like(cmd)
    obs[0] = cmd[0]
    for i in range(1, len(cmd)):
        obs[i] = obs[i - 1] + 0.5 * (cmd[i - 1] - obs[i - 1])
    t = np.arange(len(cmd)) / hz
    # task context = what perception would provide (here: pick/place poses in joint space)
    context = np.r_[pick, place].astype(np.float32)
    return {"t": t, "obs": obs, "action": cmd, "context": context, "success": np.array(True)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="datasets/synthetic_pick_place")
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    for i in range(args.episodes):
        np.savez(os.path.join(args.out, f"episode_{i:04d}.npz"), **make_episode(rng))
    print(f"wrote {args.episodes} episodes -> {args.out}")


if __name__ == "__main__":
    main()
