"""Train a Behavior Cloning policy.

    python -m learning.train --config learning/configs/bc_default.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from learning.dataset import DemoDataset, list_episodes, split_episodes, validate_episode
from learning.models import BCPolicy


def run(cfg: dict) -> dict:
    torch.manual_seed(cfg["seed"])
    np.random.seed(cfg["seed"])
    os.makedirs(cfg["out_dir"], exist_ok=True)

    paths = [p for p in list_episodes(cfg["data_dir"]) if validate_episode(p).ok]
    if len(paths) < 2:
        raise SystemExit(f"need >=2 valid episodes in {cfg['data_dir']}")
    train_p, val_p = split_episodes(paths, cfg["val_ratio"], cfg["seed"])
    mode = cfg.get("action_mode", "delta")
    train_ds = DemoDataset(train_p, cfg["history"], cfg["horizon"], mode)
    val_ds = DemoDataset(val_p, cfg["history"], cfg["horizon"], mode)

    obs_dim, act_dim = train_ds[0][0].shape[-1], train_ds[0][1].shape[-1]
    model = BCPolicy(obs_dim, act_dim, cfg["history"], cfg["hidden"], cfg["layers"], cfg["dropout"], mode)
    model.set_normalization(*train_ds.stats())

    tl = DataLoader(train_ds, batch_size=cfg["batch_size"], shuffle=True)
    vl = DataLoader(val_ds, batch_size=cfg["batch_size"])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, cfg["epochs"])
    loss_fn = nn.MSELoss()
    norm = lambda a: (a - model.act_mean) / model.act_std  # noqa: E731

    history, best = [], float("inf")
    for epoch in range(1, cfg["epochs"] + 1):
        model.train()
        tr = 0.0
        for o, a in tl:
            loss = loss_fn(model(o), norm(a))
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tr += loss.item() * len(o)
        sched.step()
        model.eval()
        va, mae = 0.0, 0.0
        with torch.no_grad():
            for o, a in vl:
                va += loss_fn(model(o), norm(a)).item() * len(o)
                mae += ((model(o) - norm(a)) * model.act_std).abs().mean().item() * len(o)
        row = {"epoch": epoch, "train_loss": tr / len(train_ds), "val_loss": va / len(val_ds),
               "val_mae_rad": mae / len(val_ds)}
        history.append(row)
        if row["val_loss"] < best:
            best = row["val_loss"]
            torch.save({"config": model.config(), "state_dict": model.state_dict(), "train_cfg": cfg,
                        "val_episodes": val_p}, os.path.join(cfg["out_dir"], "best.pt"))
        if epoch == 1 or epoch % 10 == 0 or epoch == cfg["epochs"]:
            print(f"ep {epoch:3d}  train {row['train_loss']:.4f}  val {row['val_loss']:.4f}  "
                  f"val_mae {row['val_mae_rad']:.4f} rad")

    with open(os.path.join(cfg["out_dir"], "loss_history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0]))
        w.writeheader()
        w.writerows(history)
    summary = {"train_episodes": len(train_p), "val_episodes": len(val_p), "best_val_loss": best,
               "final": history[-1]}
    with open(os.path.join(cfg["out_dir"], "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="learning/configs/bc_default.json")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--data_dir")
    ap.add_argument("--out_dir")
    args = ap.parse_args()
    with open(args.config) as f:
        cfg = json.load(f)
    for k in ("epochs", "data_dir", "out_dir"):
        if getattr(args, k) is not None:
            cfg[k] = getattr(args, k)
    print(json.dumps(run(cfg), indent=2))


if __name__ == "__main__":
    main()
