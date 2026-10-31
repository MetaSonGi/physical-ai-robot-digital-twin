import numpy as np

from safety_controller.safety_filter import SafetyConfig, SafetyFilter

HOME = np.array([0.0, -1.0, 0.3, 0.7, 0.01])


def make():
    return SafetyFilter(SafetyConfig(max_vel=[1.0] * 4 + [0.05], timeout_s=0.3))


def test_passes_small_valid_step():
    step = np.array([0.01, 0.01, 0.01, 0.01, 0.0])
    r = make().step(HOME, HOME + step, target_age_s=0.0, dt=0.05)
    assert r.status == "ok"
    np.testing.assert_allclose(r.command, HOME + step)


def test_clamps_joint_limits():
    tgt = HOME.copy(); tgt[0] = 10.0
    f = make()
    cur = HOME.copy()
    for _ in range(200):
        cur = f.step(cur, tgt, 0.0, 0.05).command
    assert cur[0] <= f.upper[0] + 1e-9


def test_rate_limits_large_jump():
    tgt = HOME.copy(); tgt[1] = 1.0
    r = make().step(HOME, tgt, 0.0, dt=0.05)
    assert r.status == "rate_limited"
    assert abs(r.command[1] - HOME[1]) <= 1.0 * 0.05 + 1e-9


def test_estop_holds_position():
    f = make(); f.set_estop(True)
    r = f.step(HOME, HOME + 0.5, 0.0, 0.05)
    assert r.status == "estop"
    np.testing.assert_allclose(r.command, HOME)


def test_stale_and_invalid_targets_hold():
    f = make()
    assert f.step(HOME, HOME + 0.1, target_age_s=1.0, dt=0.05).status == "stale"
    assert f.step(HOME, None, 0.0, 0.05).status == "stale"
    bad = HOME.copy(); bad[2] = np.nan
    assert f.step(HOME, bad, 0.0, 0.05).status == "invalid"
