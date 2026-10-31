"""Plot train/val loss from runs/<name>/loss_history.csv.

    python -m learning.plot_loss runs/bc_default --out docs/images/loss_curve.png
"""
import argparse
import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(os.path.join(a.run_dir, "loss_history.csv"))))
    ep = [int(r["epoch"]) for r in rows]
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=130)
    ax.plot(ep, [float(r["train_loss"]) for r in rows], label="train", color="#2563eb", lw=2)
    ax.plot(ep, [float(r["val_loss"]) for r in rows], label="val (held-out episodes)", color="#ea580c", lw=2)
    ax.set_xlabel("epoch"); ax.set_ylabel("MSE (normalized delta action)")
    ax.set_title("Behavior Cloning — synthetic pick & place")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(alpha=.25); ax.legend(frameon=False)
    fig.tight_layout()
    out = a.out or os.path.join(a.run_dir, "loss_curve.png")
    fig.savefig(out)
    print("saved", out)


if __name__ == "__main__":
    main()
