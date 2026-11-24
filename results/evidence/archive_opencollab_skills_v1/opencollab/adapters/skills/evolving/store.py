"""``SkillStorePort`` over a ``SkillLibrary``: only trial and active skills load."""

from __future__ import annotations

import logging
import os

from opencollab.adapters.skills.evolving.library import LibraryError, SkillLibrary
from opencollab.adapters.skills.file_skill_store import SKILL_BODY_MAX_CHARS, SKILL_DESCRIPTION_MAX_CHARS
from opencollab.adapters.tools._output import truncate
from opencollab.domain.skill import SkillManifest

logger = logging.getLogger(__name__)


class EvolvingSkillStore:
    """Read the library once at construction, like ``FileSkillStore``.

    Each session builds its own store, so a library edited between runs is
    picked up by the next run while a running session keeps a stable catalog.
    """

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._manifests: list[SkillManifest] = []
        self._bodies: dict[str, str] = {}
        self.load_diagnostics: list[str] = []
        library = SkillLibrary(root)
        for name in library.loadable_names():
            try:
                description, body = library.read(name)
            except (OSError, UnicodeDecodeError, LibraryError) as exc:
                self.load_diagnostics.append(f"skill {name!r} skipped: {exc}")
                logger.warning("skipping skill %s in %s: %s", name, root, exc)
                continue
            if len(body) > SKILL_BODY_MAX_CHARS:
                self.load_diagnostics.append(f"skill {name!r} skipped: body exceeds {SKILL_BODY_MAX_CHARS} chars")
                continue
            description = truncate(description, SKILL_DESCRIPTION_MAX_CHARS)
            self._manifests.append(SkillManifest(name=name, description=description))
            self._bodies[name] = body

    def list_manifests(self) -> tuple[SkillManifest, ...]:
        return tuple(self._manifests)

    def get_body(self, name: str) -> str | None:
        return self._bodies.get(name)


__all__ = ["EvolvingSkillStore"]
