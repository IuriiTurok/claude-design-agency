#!/usr/bin/env python3
"""measure() realized-data tests for the impeccable anti-pattern adapter.

The comparable metric + gates stay fixture-based (detector quality); the deepening
adds REAL observed-violation prevalence (ai-slop-candidates.jsonl) to detail ONLY
— never a gate, since for a ban fewer real observations is success. Plain asserts:
python3 sil/test_measure.py
"""

import importlib.util
import json
import os
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "imp_loop", os.path.join(HERE, "impeccable_loop.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _row(ts, pid="glassmorphism"):
    return types.SimpleNamespace(
        ts=ts, change_signature=f"imp-antipattern:{pid}", baseline_metric=0.0
    )


def test_fixture_only():
    """No real candidates file -> source 'fixture', prevalence 0, gates unchanged."""
    m.CANDIDATES = os.path.join(tempfile.gettempdir(), "imp-no-such-candidates.jsonl")
    if os.path.exists(m.CANDIDATES):
        os.remove(m.CANDIDATES)
    res = m.ImpeccableAdapter().measure(_row("2026-06-01T00:00:00Z"))
    assert res.detail["source"] == "fixture", res.detail
    assert res.detail["real_observed_in_window"] == 0, res.detail
    assert set(res.gates) == {
        "no_false_positive_on_goldens",
        "catches_the_bad_fixture",
    }, res.gates
    print("  fixture-only OK")


def test_real_observed():
    """Real candidates present -> windowed prevalence in detail, never a gate."""
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        # before window (excluded), in window (counted), other pid (ignored)
        f.write(
            json.dumps({"ts": "2026-05-01T00:00:00Z", "pattern_id": "glassmorphism"})
            + "\n"
        )
        f.write(
            json.dumps({"ts": "2026-06-10T00:00:00Z", "pattern_id": "glassmorphism"})
            + "\n"
        )
        f.write(
            json.dumps({"ts": "2026-06-11T00:00:00Z", "pattern_id": "side-stripe-border"})
            + "\n"
        )
        path = f.name
    m.CANDIDATES = path
    try:
        res = m.ImpeccableAdapter().measure(_row("2026-06-05T00:00:00Z"))
    finally:
        os.remove(path)
    assert res.detail["source"] == "real+fixture", res.detail
    assert res.detail["real_observed_in_window"] == 1, res.detail  # only in-window match
    assert not any("real" in g for g in res.gates), res.gates  # prevalence is not a gate
    print("  real-observed OK")


if __name__ == "__main__":
    test_fixture_only()
    test_real_observed()
    print("impeccable measure(): ALL PASS")
