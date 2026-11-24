"""Accept an edit only when it wins on held-out runs (EvoSkill, arXiv 2603.02766).

An LLM can rank finished skills but predicts the effect of a single edit poorly
(arXiv 2609.39148), so every edit is decided by running it. Arms are compared
pairwise on ``(task, rep)``; only discordant pairs carry information.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable

from opencollab.adapters.skills.evolving.evidence import RunOutcome


@dataclass(frozen=True)
class GateDecision:
    accept: bool
    wins: int
    losses: int
    pairs: int
    p_value: float
    reason: str


def sign_test(wins: int, losses: int) -> float:
    """Two-sided exact sign test on discordant pairs."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired(baseline: Iterable[RunOutcome], candidate: Iterable[RunOutcome]) -> tuple[int, int, int]:
    """Return ``(wins, losses, pairs)`` of candidate against baseline."""
    base = {(o.task, o.rep): o.resolved for o in baseline}
    wins = losses = pairs = 0
    for o in candidate:
        key = (o.task, o.rep)
        if key not in base:
            continue
        pairs += 1
        if o.resolved and not base[key]:
            wins += 1
        elif base[key] and not o.resolved:
            losses += 1
    return wins, losses, pairs


def decide(baseline: Iterable[RunOutcome], candidate: Iterable[RunOutcome], *, min_margin: int = 1) -> GateDecision:
    """Accept when wins exceed losses by ``min_margin``; ties are rejected."""
    wins, losses, pairs = paired(baseline, candidate)
    p = sign_test(wins, losses)
    accept = pairs > 0 and wins - losses >= min_margin
    verdict = "accepted" if accept else "rejected"
    return GateDecision(accept, wins, losses, pairs, p, f"{verdict}: {wins} wins, {losses} losses over {pairs} pairs")


__all__ = ["GateDecision", "decide", "paired", "sign_test"]
