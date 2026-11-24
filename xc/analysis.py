"""Pure decision logic for CrossCheck (no I/O, no LLM). Unit-tested offline.

Inputs are per-test-case outcomes: dict nodeid -> "pass" | "fail" | "error".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_REQ = re.compile(r"test_r(\d+)", re.I)


def requirement_ids(cases: dict[str, str] | list[str]) -> set[int]:
    """Requirement ids referenced by test names such as test_r3_negative_total."""
    names = cases.keys() if isinstance(cases, dict) else cases
    return {int(m.group(1)) for n in names for m in [_REQ.search(n.split("::")[-1])] if m}


@dataclass
class SuiteQuality:
    """Quality of the independent (Test Designer) suite, measured before use."""

    cases: int
    on_base_pass: int  # cases already passing on the untouched base (no signal vs base)
    covered: int  # requirements referenced by at least one test name
    requirements: int
    collect_error: str | None = None

    @property
    def coverage(self) -> float:
        return self.covered / self.requirements if self.requirements else 0.0

    @property
    def usable(self) -> bool:
        return self.collect_error is None and self.cases > 0

    def credible_for_stop(self, min_cases: int = 4, min_coverage: float = 0.6) -> bool:
        """Is the suite strong enough to stop after one candidate?

        A passing result is only informative if the suite could have failed:
        enough cases, broad requirement coverage, and most cases must fail on
        the base (otherwise they test nothing the task asks to change).
        """
        if not self.usable or self.cases < min_cases:
            return False
        discriminating = self.cases - self.on_base_pass
        # Without a contract there is no requirement inventory to cover; fall back
        # to size and discrimination only (h1_cron r9: the spec was cut off).
        coverage_ok = self.coverage >= min_coverage if self.requirements else self.cases >= 2 * min_cases
        # v2.2: on bug-fix tasks most specified behavior already works on the base,
        # so many valid tests pass there (t1_semver r0: 22 of 103 failed on base, all
        # 103 valid). Require enough tests that probe changed behavior, not a majority.
        return coverage_ok and discriminating >= max(3, self.cases // 5)


def suite_quality(base_outcome: dict[str, str], n_requirements: int, collect_error: str | None) -> SuiteQuality:
    covered = requirement_ids(base_outcome) & set(range(1, n_requirements + 1))
    return SuiteQuality(
        cases=len(base_outcome),
        on_base_pass=sum(1 for v in base_outcome.values() if v == "pass"),
        covered=len(covered),
        requirements=n_requirements,
        collect_error=collect_error,
    )


@dataclass
class Matrix:
    """Cross-execution matrix: test source -> candidate -> case outcomes."""

    cells: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)

    def set(self, source: str, candidate: str, outcome: dict[str, str]) -> None:
        self.cells.setdefault(source, {})[candidate] = outcome

    def get(self, source: str, candidate: str) -> dict[str, str]:
        return self.cells.get(source, {}).get(candidate, {})


def witnesses(matrix: Matrix, source: str, candidates: list[str], min_rate: float = 0.5,
              exclude: set[str] = frozenset()) -> list[str]:
    """Candidates plausible enough to testify against a test.

    v1 counted every candidate. In h1_cron r9, coder B's session was cut off by
    the provider and its broken code failed all 133 tests, which made every
    test that A failed look "suspect". A candidate only counts as a witness if
    it passes at least `min_rate` of the (non-excluded) independent cases.
    """
    out = []
    for c in candidates:
        o = {k: v for k, v in matrix.get(source, c).items() if k not in exclude}
        if o and sum(v == "pass" for v in o.values()) / len(o) >= min_rate:
            out.append(c)
    return out


def suspect_cases(matrix: Matrix, source: str, candidates: list[str], exclude: set[str] = frozenset()) -> set[str]:
    """Independent-test cases that every plausible independent candidate fails.

    Two implementers who never saw each other's work (nor the tests) both
    disagreeing with a test is evidence the test, not the code, is wrong
    (TEX: "if agent i's test fails on all patches, it may be overly strict").
    With fewer than two witnesses this signal does not exist.
    """
    wit = witnesses(matrix, source, candidates, exclude=exclude)
    if len(wit) < 2:
        return set()
    outcomes = [matrix.get(source, c) for c in wit]
    keys = set().union(*(o.keys() for o in outcomes))
    return {k for k in keys if all(o.get(k, "fail") != "pass" for o in outcomes)}


def peer_cases(matrix: Matrix, author: str, other: str) -> dict[str, str]:
    """Author-written tests that the author's own code passes, run on the other candidate.

    Tests that fail on their own author carry no reliable expectation.
    """
    own = matrix.get(f"own:{author}", author)
    on_other = matrix.get(f"own:{author}", other)
    return {k: on_other.get(k, "fail") for k, v in own.items() if v == "pass"}


@dataclass
class Score:
    candidate: str
    indep_pass: int
    indep_total: int
    peer_pass: int
    peer_total: int
    own_fail: int

    @property
    def key(self) -> tuple:
        # independent tests first (frozen, author-blind), then peer tests,
        # then fewer failures of the candidate's own tests
        return (self.indep_pass, self.peer_pass, -self.own_fail)

    @property
    def clean(self) -> bool:
        return self.indep_pass == self.indep_total and self.peer_pass == self.peer_total and self.own_fail == 0


def score(matrix: Matrix, cand: str, peers: list[str], suspects: set[str]) -> Score:
    indep = {k: v for k, v in matrix.get("indep", cand).items() if k not in suspects}
    peer_pass = peer_total = 0
    for p in peers:
        if p == cand:
            continue
        cases = peer_cases(matrix, p, cand)
        peer_total += len(cases)
        peer_pass += sum(1 for v in cases.values() if v == "pass")
    own = matrix.get(f"own:{cand}", cand)
    return Score(
        candidate=cand,
        indep_pass=sum(1 for v in indep.values() if v == "pass"),
        indep_total=len(indep),
        peer_pass=peer_pass,
        peer_total=peer_total,
        own_fail=sum(1 for v in own.values() if v != "pass"),
    )


def disagreements(matrix: Matrix, a: str, b: str, suspects: set[str]) -> list[tuple[str, str, str, str]]:
    """(source, case, outcome_a, outcome_b) where the two candidates differ."""
    out = []
    for source, by_cand in matrix.cells.items():
        oa, ob = by_cand.get(a), by_cand.get(b)
        if oa is None or ob is None:
            continue
        for k in sorted(set(oa) | set(ob)):
            if source == "indep" and k in suspects:
                continue
            va, vb = oa.get(k, "fail"), ob.get(k, "fail")
            if (va == "pass") != (vb == "pass"):
                out.append((source, k, va, vb))
    return out


def failing_for(matrix: Matrix, cand: str, peers: list[str], suspects: set[str]) -> dict[str, list[str]]:
    """Failing evidence to hand a candidate's repairer, grouped by source."""
    out: dict[str, list[str]] = {}
    indep = matrix.get("indep", cand)
    out["independent"] = sorted(k for k, v in indep.items() if v != "pass" and k not in suspects)
    out["contested"] = sorted(k for k in suspects if indep.get(k, "fail") != "pass")
    peer_fail = []
    for p in peers:
        if p != cand:
            peer_fail += [f"{p}:{k}" for k, v in peer_cases(matrix, p, cand).items() if v != "pass"]
    out["peer"] = sorted(peer_fail)
    own = matrix.get(f"own:{cand}", cand)
    out["own"] = sorted(k for k, v in own.items() if v != "pass")
    return out
