"""Give every tool-using session the skill catalog and ``use_skill``.

Upstream exposes skills only to team roles that list ``use_skill`` (by default
the Analyst), reading ``<workspace>/skills``. Workflow agents (Duo, Weave,
authored workflows) and ``OpenCollab.agent`` sessions never see a skill. When
``OPENCOLLAB_SKILLS_DIR`` names a library, ``attach_skills`` runs inside
``build_session`` and closes that gap for every mode at once.

Rules, chosen so that an unset variable or an empty library changes nothing:

- no ``OPENCOLLAB_SKILLS_DIR`` or no loadable skill: the agent is returned as is;
- a session without tools stays without tools (e.g. a judge with ``tools=[]``);
- a session that already has ``use_skill`` keeps it; ``build_skill_store``
  points that tool at the same library.
"""

from __future__ import annotations

import copy
import os
from typing import Any

from opencollab.adapters.skills.evolving.store import EvolvingSkillStore
from opencollab.adapters.tools.use_skill import UseSkillTool
from opencollab.domain.context import ContextLayer, ContextPlan, ContextPosition, ContextSource
from opencollab.domain.skill import SkillManifest

SKILLS_DIR_ENV = "OPENCOLLAB_SKILLS_DIR"


def skills_dir() -> str | None:
    value = os.environ.get(SKILLS_DIR_ENV, "").strip()
    return value or None


def render_catalog(manifests: tuple[SkillManifest, ...]) -> str:
    # Same wording as the team catalog, so both modes present skills alike.
    lines = [
        "## Skills",
        "",
        "Specialized instruction sets you can load on demand. When one matches "
        "the task, call `use_skill(name)` to pull its full instructions into "
        "your context.",
        "",
    ]
    lines += [f"- {m.name}: {m.description}" for m in manifests]
    return "\n".join(lines)


def attach_skills(
    agent: Any,
    seed_system_messages: list[dict[str, Any]] | None,
) -> tuple[Any, list[dict[str, Any]] | None]:
    """Return ``(agent, seed_system_messages)``, extended when skills apply."""
    root = skills_dir()
    tools = list(getattr(agent, "tools", ()) or ())
    if root is None or not tools or any(getattr(t, "name", None) == "use_skill" for t in tools):
        return agent, seed_system_messages
    store = EvolvingSkillStore(root)
    manifests = store.list_manifests()
    if not manifests:
        return agent, seed_system_messages
    catalog = render_catalog(manifests)
    extended = copy.copy(agent)
    extended.tools = [*tools, UseSkillTool(store)]
    extended.system_prompt = f"{agent.system_prompt}\n\n{catalog}"
    if seed_system_messages:
        source = ContextSource(
            name="skills", layer=ContextLayer.SKILL, position=ContextPosition.SYSTEM, content=catalog
        )
        seed_system_messages = [*seed_system_messages, *ContextPlan(sources=(source,)).startup_system_messages()]
    return extended, seed_system_messages


__all__ = ["SKILLS_DIR_ENV", "attach_skills", "render_catalog", "skills_dir"]
