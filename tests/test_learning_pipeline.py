import json

import numpy as np
import torch

from learning.dataset import DemoDataset, list_episodes, split_episodes, validate_episode
from learning.evaluate import evaluate
from learning.generate_synthetic import make_episode
from learning.models import BCPolicy
from learning.train import run


def _write(tmp_path, n=6):
    rng = np.random.default_rng(0)
    for i in range(n):
        np.savez(tmp_path / f"episode_{i:04d}.npz", **make_episode(rng))
    return str(tmp_path)


def test_validation_rejects_bad_episode(tmp_path):
    d = _write(tmp_path, 1)
    ep = dict(np.load(f"{d}/episode_0000.npz"))
    ep["obs"][5, 0] = np.nan
    np.savez(tmp_path / "episode_0001.npz", **ep)
    reports = [validate_episode(p) for p in list_episodes(d)]
    assert [r.ok for r in reports] == [True, False]


def test_split_is_by_episode(tmp_path):
    paths = list_episodes(_write(tmp_path, 10))
    tr, va = split_episodes(paths, 0.2, seed=1)
    assert len(va) == 2 and not set(tr) & set(va)


def test_dataset_shapes_include_context(tmp_path):
    ds = DemoDataset(list_episodes(_write(tmp_path, 2)), history=4)
    o, a = ds[0]
    assert o.shape == (4, 5 + 8) and a.shape == (5,)


def test_policy_roundtrip_and_delta_predict(tmp_path):
    m = BCPolicy(obs_dim=13, act_dim=5, history=4, hidden=32, layers=2)
    for p in m.head.parameters():
        torch.nn.init.zeros_(p)  # zero output -> delta 0 -> predict == current joints
    x = torch.randn(3, 4, 13)
    np.testing.assert_allclose(m.predict(x).numpy(), x[:, -1, :5].numpy(), atol=1e-6)
    path = tmp_path / "m.pt"
    torch.save({"config": m.config(), "state_dict": m.state_dict()}, path)
    m2 = BCPolicy.load(str(path))
    np.testing.assert_allclose(m2.predict(x).numpy(), m.predict(x).numpy(), atol=1e-6)


def test_train_and_evaluate_smoke(tmp_path):
    (tmp_path / "data").mkdir()
    d = _write(tmp_path / "data", 6)
    out = tmp_path / "run"
    cfg = json.load(open("learning/configs/bc_default.json"))
    cfg.update(data_dir=d, out_dir=str(out), epochs=3, hidden=32, layers=2, batch_size=64)
    summary = run(cfg)
    assert np.isfinite(summary["best_val_loss"])
    assert (out / "best.pt").exists() and (out / "loss_history.csv").exists()
    metrics = evaluate(str(out / "best.pt"))
    assert 0.0 <= metrics["closed_loop_success_rate"] <= 1.0
