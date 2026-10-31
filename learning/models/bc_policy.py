"""Behavior Cloning policy: observation history -> next joint target (absolute or delta)."""
from __future__ import annotations

import torch
from torch import nn


class BCPolicy(nn.Module):
    """MLP policy with built-in input/output normalization.

    Input : (B, history, obs_dim)  - recent joint positions (+ gripper)
    Output: (B, act_dim)           - next joint target; "delta" mode predicts target - current joints
    """

    def __init__(self, obs_dim: int, act_dim: int, history: int = 4,
                 hidden: int = 256, layers: int = 3, dropout: float = 0.1, action_mode: str = "delta"):
        super().__init__()
        self.obs_dim, self.act_dim, self.history = obs_dim, act_dim, history
        self.action_mode = action_mode
        dims = [obs_dim * history] + [hidden] * layers
        blocks: list[nn.Module] = []
        for i in range(layers):
            blocks += [nn.Linear(dims[i], dims[i + 1]), nn.LayerNorm(dims[i + 1]), nn.GELU(), nn.Dropout(dropout)]
        self.backbone = nn.Sequential(*blocks)
        self.head = nn.Linear(hidden, act_dim)

        # Normalization stats are buffers so they are saved with the checkpoint.
        self.register_buffer("obs_mean", torch.zeros(obs_dim))
        self.register_buffer("obs_std", torch.ones(obs_dim))
        self.register_buffer("act_mean", torch.zeros(act_dim))
        self.register_buffer("act_std", torch.ones(act_dim))

    def set_normalization(self, obs_mean, obs_std, act_mean, act_std) -> None:
        for name, v in [("obs_mean", obs_mean), ("obs_std", obs_std), ("act_mean", act_mean), ("act_std", act_std)]:
            getattr(self, name).copy_(torch.as_tensor(v, dtype=torch.float32))

    def forward(self, obs_hist: torch.Tensor) -> torch.Tensor:
        """Returns normalized action. Use `predict` for raw joint values."""
        x = (obs_hist - self.obs_mean) / self.obs_std
        return self.head(self.backbone(x.flatten(1)))

    @torch.no_grad()
    def predict(self, obs_hist: torch.Tensor) -> torch.Tensor:
        """Absolute joint target in robot units, regardless of action_mode."""
        self.eval()
        out = self.forward(obs_hist) * self.act_std + self.act_mean
        if self.action_mode == "delta":
            out = out + obs_hist[:, -1, : self.act_dim]
        return out

    def config(self) -> dict:
        return {"obs_dim": self.obs_dim, "act_dim": self.act_dim, "history": self.history,
                "hidden": self.head.in_features, "layers": sum(isinstance(m, nn.Linear) for m in self.backbone),
                "action_mode": self.action_mode}

    @classmethod
    def load(cls, path: str, map_location: str = "cpu") -> "BCPolicy":
        ckpt = torch.load(path, map_location=map_location, weights_only=False)
        model = cls(**ckpt["config"])
        model.load_state_dict(ckpt["state_dict"])
        model.eval()
        return model
