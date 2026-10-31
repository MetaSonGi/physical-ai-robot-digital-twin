"""Pure-Python safety filter (no ROS dependency -> unit-testable in CI).

Every policy target passes through `SafetyFilter.step()` before reaching the motors:
  1. E-stop latched          -> hold current position
  2. Stale / NaN input       -> hold current position
  3. Joint position limits   -> clamp
  4. Per-step velocity limit -> rate-limit toward target
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# OpenMANIPULATOR-X joint limits [rad] (joint1..joint4) and gripper [m]. Verify against your URDF.
DEFAULT_LOWER = [-2.82, -1.79, -0.94, -1.79, -0.010]
DEFAULT_UPPER = [2.82, 1.57, 1.38, 2.04, 0.019]


@dataclass
class SafetyConfig:
    lower: list[float] = field(default_factory=lambda: list(DEFAULT_LOWER))
    upper: list[float] = field(default_factory=lambda: list(DEFAULT_UPPER))
    max_vel: list[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 0.05])  # units/s
    timeout_s: float = 0.3


@dataclass
class SafetyResult:
    command: np.ndarray
    status: str  # "ok" | "clamped" | "rate_limited" | "estop" | "stale" | "invalid"


class SafetyFilter:
    def __init__(self, cfg: SafetyConfig | None = None):
        self.cfg = cfg or SafetyConfig()
        self.lower = np.asarray(self.cfg.lower, dtype=float)
        self.upper = np.asarray(self.cfg.upper, dtype=float)
        self.max_vel = np.asarray(self.cfg.max_vel, dtype=float)
        self.estop = False

    def set_estop(self, engaged: bool) -> None:
        self.estop = bool(engaged)

    def step(self, current: np.ndarray, target: np.ndarray | None, target_age_s: float, dt: float) -> SafetyResult:
        current = np.asarray(current, dtype=float)
        if self.estop:
            return SafetyResult(current.copy(), "estop")
        if target is None or target_age_s > self.cfg.timeout_s:
            return SafetyResult(current.copy(), "stale")
        target = np.asarray(target, dtype=float)
        if target.shape != current.shape or not np.isfinite(target).all():
            return SafetyResult(current.copy(), "invalid")

        status = "ok"
        clamped = np.clip(target, self.lower, self.upper)
        if not np.allclose(clamped, target):
            status = "clamped"
        max_step = self.max_vel * max(dt, 1e-3)
        delta = np.clip(clamped - current, -max_step, max_step)
        if not np.allclose(delta, clamped - current):
            status = "rate_limited" if status == "ok" else status
        return SafetyResult(current + delta, status)
