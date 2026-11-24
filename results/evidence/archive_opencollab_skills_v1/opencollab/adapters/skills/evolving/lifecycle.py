"""Outcome-driven promotion and retirement (Library Drift, arXiv 2605.19576; SkillForge, 2610.09832).

Usage statistics only nominate a skill. Runs that load a skill are not a
random sample (the agent loads it on tasks it finds hard), so a lower resolve
rate among them is a hint, not proof. A nominated skill is retired only after
a leave-one-out gate: the library without it must not lose to the library with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from opencollab.adapters.skills.evolving.evidence import RunOutcome, resolve_rate
from opencollab.adapters.skills.evolving.library import SkillLibrary


@dataclass(frozen=True)
class SkillUsage:
    name: str
    runs_loaded: int
    rate_loaded: float | None
    rate_not_loaded: float | None


@dataclass(frozen=True)
class Nomination:
    action: str  # "promote" | "ablate"
    skill: str
    reason: str


def usage(library: SkillLibrary, outcomes: Iterable[RunOutcome]) -> list[SkillUsage]:
    items = list(outcomes)
    result = []
    for name in library.loadable_names():
        loaded = [o for o in items if name in o.skills_used]
        others = [o for o in items if name not in o.skills_used]
        result.append(SkillUsage(name, len(loaded), resolve_rate(loaded), resolve_rate(others)))
    return result


def nominate(library: SkillLibrary, outcomes: Iterable[RunOutcome], *, min_uses: int = 3) -> list[Nomination]:
    """Promote trial skills that agents load; nominate rarely helpful active skills for ablation.

    A trial skill reaches this point only after passing its gate in an earlier
    round, so being loaded again on fresh runs is enough to promote it.
    A trial skill nobody loads stays trial; it costs only one catalog line.
    """
    records = library.records()
    nominations = []
    for item in usage(library, outcomes):
        status = records[item.name].status if item.name in records else "manual"
        if status == "trial" and item.runs_loaded >= 1:
            nominations.append(Nomination("promote", item.name, f"loaded in {item.runs_loaded} runs after its gate"))
        if (status == "active" and item.runs_loaded >= min_uses and item.rate_loaded is not None
                and item.rate_not_loaded is not None and item.rate_loaded < item.rate_not_loaded):
            nominations.append(Nomination(
                "ablate", item.name,
                f"resolve rate {item.rate_loaded:.0%} when loaded vs {item.rate_not_loaded:.0%} otherwise "
                f"over {item.runs_loaded} loading runs",
            ))
    return nominations


__all__ = ["Nomination", "SkillUsage", "nominate", "usage"]
