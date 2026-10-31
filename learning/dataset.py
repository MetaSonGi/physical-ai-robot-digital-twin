"""Demonstration dataset utilities.

Episode format (datasets/<task>/episode_XXXX.npz):
    t      : (T,)          float64  timestamps [s]
    obs    : (T, obs_dim)  float32  follower joint positions [rad] + gripper
    action : (T, act_dim)  float32  leader joint command at the same tick
    context: (C,)          float32  task context, e.g. object/goal pose from perception (optional)
    success: ()            bool     operator label (optional, default True)

The policy observation per frame is concat(obs[t], context) -> obs_dim + C.
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass

import numpy as np
import torch
from torch.utils.data import Dataset

JOINT_NAMES = ["joint1", "joint2", "joint3", "joint4", "gripper"]


@dataclass
class ValidationReport:
    path: str
    ok: bool
    reasons: list[str]


def validate_episode(path: str, min_len: int = 20, max_gap_s: float = 0.2,
                     joint_limit: float = 3.2) -> ValidationReport:
    """Reject broken demonstrations before they poison training."""
    reasons: list[str] = []
    try:
        ep = np.load(path)
        t, obs, act = ep["t"], ep["obs"], ep["action"]
    except Exception as e:  # noqa: BLE001
        return ValidationReport(path, False, [f"unreadable: {e}"])
    if len(obs) < min_len:
        reasons.append(f"too short ({len(obs)} < {min_len})")
    if len(obs) != len(act) or len(obs) != len(t):
        reasons.append("length mismatch between t/obs/action")
    if not (np.isfinite(obs).all() and np.isfinite(act).all()):
        reasons.append("NaN/Inf values")
    if len(t) > 1 and np.diff(t).max() > max_gap_s:
        reasons.append(f"timestamp gap {np.diff(t).max():.3f}s > {max_gap_s}s")
    if np.abs(obs).max() > joint_limit:
        reasons.append("joint value outside physical range")
    if "success" in ep.files and not bool(ep["success"]):
        reasons.append("labelled as failed demonstration")
    return ValidationReport(path, not reasons, reasons)


def load_episode(path: str):
    """Returns (policy_obs, action) where policy_obs already includes the task context."""
    ep = np.load(path)
    obs, act = ep["obs"].astype(np.float32), ep["action"].astype(np.float32)
    if "context" in ep.files:
        ctx = np.broadcast_to(ep["context"].astype(np.float32), (len(obs), ep["context"].shape[-1]))
        obs = np.concatenate([obs, ctx], axis=1)
    return obs, act


def list_episodes(data_dir: str) -> list[str]:
    return sorted(glob.glob(os.path.join(data_dir, "episode_*.npz")))


def split_episodes(paths: list[str], val_ratio: float = 0.2, seed: int = 0):
    """Split by *episode* (not by frame) to avoid leakage between train/val."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(paths))
    n_val = max(1, int(round(len(paths) * val_ratio))) if len(paths) > 1 else 0
    val = [paths[i] for i in idx[:n_val]]
    train = [paths[i] for i in idx[n_val:]]
    return train, val


class DemoDataset(Dataset):
    """Sliding window: obs[t-H+1 : t+1] -> action[t + horizon]."""

    def __init__(self, paths: list[str], history: int = 4, horizon: int = 1, action_mode: str = "delta"):
        """action_mode: "absolute" -> target = action[t+h]
                        "delta"    -> target = action[t+h] - obs[t, :act_dim]  (easier to generalize)"""
        assert action_mode in ("absolute", "delta")
        self.history, self.horizon, self.action_mode = history, horizon, action_mode
        self.samples: list[tuple[np.ndarray, np.ndarray]] = []
        for p in paths:
            obs, act = load_episode(p)
            # pad the beginning by repeating the first frame
            pad = np.repeat(obs[:1], history - 1, axis=0)
            obs_p = np.concatenate([pad, obs], axis=0)
            for t in range(len(obs) - horizon):
                target = act[t + horizon]
                if action_mode == "delta":
                    target = target - obs[t, :act.shape[1]]
                self.samples.append((obs_p[t:t + history], target))
        if not self.samples:
            raise ValueError("DemoDataset is empty - check episode paths")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, i):
        o, a = self.samples[i]
        return torch.from_numpy(o), torch.from_numpy(a)

    def stats(self):
        o = np.concatenate([s[0] for s in self.samples])
        a = np.stack([s[1] for s in self.samples])
        eps = 1e-3
        return o.mean(0), o.std(0) + eps, a.mean(0), a.std(0) + eps
