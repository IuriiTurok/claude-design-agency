#!/usr/bin/env python3
"""measure() realized-data tests for the design-agency taste-rubric adapter.

Pins all three paths of the deepened measure():
 - fixture fallback (no real file) — today's deterministic behavior, preserved;
 - real before/after (real reports on both sides of row.ts) — the realized signal,
   expressed on the baseline's scale so the kernel's gain == post_mean - pre_mean;
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
    "da_loop", os.path.join(HERE, "design-agency_loop.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _row(ts, baseline=4.0):
    return types.SimpleNamespace(
        ts=ts, change_signature="da-taste:craft", baseline_metric=baseline
    )


def _report(ts, craft):
    return json.dumps(
        {
            "engagement": ts,
            "ts": ts,
            "hard_gate_passed": True,
            "scores": {"craft": craft},
        }
    )


def _write(lines):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    f.write("\n".join(lines) + "\n")
    f.close()
    return f.name


def test_fixture_fallback():
    """No real file -> fall back to the fixture corpus, metric matches it."""
    m.REAL_REPORTS = os.path.join(tempfile.gettempdir(), "da-no-such-reports.jsonl")
    if os.path.exists(m.REAL_REPORTS):
        os.remove(m.REAL_REPORTS)
    res = m.TasteRubricAdapter().measure(_row("2026-06-01T00:00:00Z"))
    assert res.detail["source"] == "fixture-fallback", res.detail
    assert res.metric == m._mean_taste_score(m._read_reports(m.WINDOW_N)), res.metric
    print("  fixture-fallback OK")


def test_real_before_after():
    """Real reports on both sides of row.ts -> gain == post_mean - pre_mean."""
    path = _write(
        [
            _report("2026-06-01T00:00:00Z", 3.0),  # pre
            _report("2026-06-02T00:00:00Z", 3.0),  # pre
            _report("2026-06-10T00:00:00Z", 5.0),  # post
            _report("2026-06-11T00:00:00Z", 5.0),  # post
        ]
    )
    m.REAL_REPORTS = path
    try:
        res = m.TasteRubricAdapter().measure(_row("2026-06-05T00:00:00Z", baseline=4.0))
    finally:
        os.remove(path)
    assert res.detail["source"] == "real", res.detail
    assert res.detail["n_pre"] == 2 and res.detail["n_post"] == 2, res.detail
    # metric = baseline + (post_mean - pre_mean) = 4.0 + (5.0 - 3.0) = 6.0
    assert abs(res.metric - 6.0) < 1e-9, res.metric
    assert res.gates["hard_gate_not_worse"] is True, res.gates
    print("  real-before-after OK")


def test_real_post_only_falls_back():
    """Real post-apply reports but no pre-apply baseline -> fixture fallback."""
    path = _write([_report("2026-06-10T00:00:00Z", 5.0)])
    m.REAL_REPORTS = path
    try:
        res = m.TasteRubricAdapter().measure(_row("2026-06-05T00:00:00Z"))
    finally:
        os.remove(path)
    assert res.detail["source"] == "fixture-fallback", res.detail
    print("  real-post-only-fallback OK")


def test_naive_ts_no_crash():
    """A parseable-but-tz-naive real ts must be coerced to UTC, not crash."""
    path = _write(
        [
            _report("2026-06-01T00:00:00", 3.0),  # naive pre -> coerced UTC
            _report("2026-06-10T00:00:00Z", 5.0),  # aware post
        ]
    )
    m.REAL_REPORTS = path
    try:
        res = m.TasteRubricAdapter().measure(_row("2026-06-05T00:00:00Z"))
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
    print("design-agency measure(): ALL PASS")
