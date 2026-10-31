"""Validate a demonstration folder and print a report.

    python -m learning.validate_dataset datasets/synthetic_pick_place
"""
import argparse
import sys

from learning.dataset import list_episodes, validate_episode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir")
    args = ap.parse_args()
    paths = list_episodes(args.data_dir)
    reports = [validate_episode(p) for p in paths]
    bad = [r for r in reports if not r.ok]
    for r in bad:
        print(f"[REJECT] {r.path}: {'; '.join(r.reasons)}")
    print(f"{len(reports) - len(bad)}/{len(reports)} episodes valid")
    return 0 if reports and not bad else 1


if __name__ == "__main__":
    sys.exit(main())
