#!/usr/bin/env python3
"""measure() realized-data tests for the ui-ux-pro-max reasoning adapter.

Pins all three paths of the deepened measure():
 - fixture fallback (no real file) — today's deterministic behavior, preserved;
 - real before/after (real projects for the rule on both sides of row.ts) — the
   realized override-rate change, expressed on the baseline's scale so the kernel's
   gain (baseline - metric) == pre_rate - post_rate (lower override-rate is better);
 - real-but-incomplete (post only, no pre) — degrades to the fixture re-check.
Plain asserts, no pytest:  python3 sil/test_measure.py
"""

import importlib.util
import json
import os
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "uux_loop", os.path.join(HERE, "ui-ux-pro-max_loop.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

_FIELDS = {
    "pattern": "A",
    "style": "B",
    "color_mood": "C",
    "typography_mood": "D",
    "key_effects": "E",
}


def _row(ts, rid="1", baseline=0.5):
    return types.SimpleNamespace(
        ts=ts, change_signature=f"uux-reasoning:{rid}", baseline_metric=baseline
    )


def _project(ts, overrides, rid="1"):
    return json.dumps(
        {
            "ts": ts,
            "project": ts,
            "rule_id": rid,
            "fields": dict(_FIELDS),
            "overrides": overrides,
        }
    )


def _write(lines):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    f.write("\n".join(lines) + "\n")
    f.close()
    return f.name


def test_fixture_fallback():
    """No real file -> fall back to the synthetic corpus."""
    m.REAL_PROJECTS = os.path.join(tempfile.gettempdir(), "uux-no-such-projects.jsonl")
    if os.path.exists(m.REAL_PROJECTS):
        os.remove(m.REAL_PROJECTS)
    res = m.UiUxAdapter().measure(_row("2026-06-01T00:00:00Z"))
    assert res.detail["source"] == "fixture-fallback", res.detail
    assert isinstance(res.metric, float), res.metric
    print("  fixture-fallback OK")


def test_real_before_after():
    """Real rule projects on both sides -> gain (base - metric) == pre - post rate."""
    path = _write(
        [
            # pre-apply: override-rate 0.4 (2 of 5 fields), x2
            _project("2026-06-01T00:00:00Z", {"style": "X", "pattern": "Y"}),
            _project("2026-06-02T00:00:00Z", {"style": "X", "pattern": "Y"}),
            # post-apply: override-rate 0.2 (1 of 5 fields), x2 — the edit helped
            _project("2026-06-10T00:00:00Z", {"style": "X"}),
            _project("2026-06-11T00:00:00Z", {"style": "X"}),
        ]
    )
    m.REAL_PROJECTS = path
    try:
        res = m.UiUxAdapter().measure(_row("2026-06-05T00:00:00Z", baseline=0.5))
    finally:
        os.remove(path)
    assert res.detail["source"] == "real", res.detail
    assert res.detail["n_pre"] == 2 and res.detail["n_post"] == 2, res.detail
    assert abs(res.detail["pre_rate"] - 0.4) < 1e-9, res.detail
    assert abs(res.detail["post_rate"] - 0.2) < 1e-9, res.detail
    # metric = baseline - (pre_rate - post_rate) = 0.5 - (0.4 - 0.2) = 0.3
    assert abs(res.metric - 0.3) < 1e-9, res.metric
    # gain the kernel sees (lower-is-better) = baseline - metric = 0.2 > 0 -> improvement
    assert abs((0.5 - res.metric) - 0.2) < 1e-9
    print("  real-before-after OK")


def test_real_post_only_falls_back():
    """Real post-apply projects but no pre-apply baseline -> fixture fallback."""
    path = _write([_project("2026-06-10T00:00:00Z", {"style": "X"})])
    m.REAL_PROJECTS = path
    try:
        res = m.UiUxAdapter().measure(_row("2026-06-05T00:00:00Z"))
    finally:
        os.remove(path)
    assert res.detail["source"] == "fixture-fallback", res.detail
    print("  real-post-only-fallback OK")


def test_naive_ts_no_crash():
    """A parseable-but-tz-naive real ts must be coerced to UTC, not crash."""
    path = _write(
        [
            _project("2026-06-01T00:00:00", {"style": "X", "pattern": "Y"}),  # naive pre
            _project("2026-06-10T00:00:00Z", {"style": "X"}),  # aware post
        ]
    )
    m.REAL_PROJECTS = path
    try:
        res = m.UiUxAdapter().measure(_row("2026-06-05T00:00:00Z"))
    finally:
        os.remove(path)
    assert res.detail["source"] == "real", res.detail
    assert res.detail["n_pre"] == 1 and res.detail["n_post"] == 1, res.detail
    print("  naive-ts-no-crash OK")


if __name__ == "__main__":
    test_fixture_fallback()
    test_real_before_after()
    test_real_post_only_falls_back()
    test_naive_ts_no_crash()
    print("ui-ux-pro-max measure(): ALL PASS")
