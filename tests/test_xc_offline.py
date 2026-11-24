"""Offline tests for CrossCheck decision logic and the executor (no model calls)."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xc import analysis as an  # noqa: E402
from xc import executor as ex  # noqa: E402


def test_suspect_requires_two_independent_failures():
    m = an.Matrix()
    m.set("indep", "A", {"t1": "pass", "t2": "fail", "t3": "pass", "t4": "fail"})
    m.set("indep", "B", {"t1": "pass", "t2": "fail", "t3": "pass", "t4": "pass"})
    assert an.suspect_cases(m, "indep", ["A", "B"]) == {"t2"}
    assert an.suspect_cases(m, "indep", ["A"]) == set()


def test_broken_candidate_is_not_a_witness():
    # h1_cron r9: a truncated coder B failed everything; that must not make A's
    # failures look like wrong tests.
    m = an.Matrix()
    m.set("indep", "A", {f"t{i}": "pass" for i in range(8)} | {"t8": "fail", "t9": "fail"})
    m.set("indep", "B", {f"t{i}": "fail" for i in range(10)})
    assert an.witnesses(m, "indep", ["A", "B"]) == ["A"]
    assert an.suspect_cases(m, "indep", ["A", "B"]) == set()


def test_peer_cases_drop_tests_failing_on_author():
    m = an.Matrix()
    m.set("own:A", "A", {"x": "pass", "y": "fail"})
    m.set("own:A", "B", {"x": "fail", "y": "pass"})
    assert an.peer_cases(m, "A", "B") == {"x": "fail"}


def test_score_excludes_suspects_and_orders():
    m = an.Matrix()
    m.set("indep", "A", {"t1": "pass", "t2": "fail", "t3": "fail", "t4": "pass"})
    m.set("indep", "B", {"t1": "pass", "t2": "fail", "t3": "pass", "t4": "pass"})
    sus = an.suspect_cases(m, "indep", ["A", "B"])
    assert sus == {"t2"}
    sa, sb = an.score(m, "A", ["A", "B"], sus), an.score(m, "B", ["A", "B"], sus)
    assert (sa.indep_pass, sa.indep_total) == (2, 3)
    assert (sb.indep_pass, sb.indep_total) == (3, 3)
    assert sb.key > sa.key and sb.clean and not sa.clean


def test_suite_quality_gate():
    weak = an.suite_quality({"m::test_r1_a": "fail", "m::test_r1_b": "pass"}, 5, None)
    assert not weak.credible_for_stop()
    strong = an.suite_quality({f"m::test_r{i}_x": "fail" for i in range(1, 6)}, 5, None)
    assert strong.coverage == 1.0 and strong.credible_for_stop()
    trivial = an.suite_quality({f"m::test_r{i}_x": "pass" for i in range(1, 6)}, 5, None)
    assert not trivial.credible_for_stop()  # passes on base: could not have failed


def test_disagreements_skip_suspects():
    m = an.Matrix()
    m.set("indep", "A", {"t1": "pass", "t2": "fail"})
    m.set("indep", "B", {"t1": "fail", "t2": "fail"})
    assert an.disagreements(m, "A", "B", {"t2"}) == [("indep", "t1", "pass", "fail")]


def _repo(tmp: Path) -> Path:
    ws = tmp / "ws"
    ws.mkdir()
    (ws / "m.py").write_text("def f(x):\n    return x\n")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-qm", "i"]):
        subprocess.run(cmd, cwd=ws, check=True)
    return ws


def test_executor_matrix_cell(tmp_path):
    ws = _repo(tmp_path)
    base = tmp_path / "base"
    ex.snapshot_base(ws, base)
    patch = (
        "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n@@ -1,2 +1,2 @@\n"
        " def f(x):\n-    return x\n+    return x + 1\n"
    )
    tests = {"xc_tests/test_xc_spec.py": "from m import f\n\ndef test_r1_inc():\n    assert f(1) == 2\n"}
    assert ex.run_tests(base, "", tests).failed
    out = ex.run_tests(base, patch, tests)
    assert out.passed and not out.failed
    assert ex.test_paths(patch) == []
