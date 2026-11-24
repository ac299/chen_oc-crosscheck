"""Self-evolving skills: a versioned skill library, its runtime wiring and the evolution loop.

Everything for this feature lives in this package. Outside it, two call sites
use it, both inert unless ``OPENCOLLAB_SKILLS_DIR`` is set:

- ``bootstrap.session_factory.build_session`` calls ``attach_skills``;
- ``bootstrap.container.build_skill_store`` returns an ``EvolvingSkillStore``.

See ``docs/evolving-skills.md`` for the design and the papers it follows.
"""

from opencollab.adapters.skills.evolving.attach import SKILLS_DIR_ENV, attach_skills, skills_dir
from opencollab.adapters.skills.evolving.library import LibraryError, SkillLibrary
from opencollab.adapters.skills.evolving.store import EvolvingSkillStore

__all__ = [
    "SKILLS_DIR_ENV",
    "EvolvingSkillStore",
    "LibraryError",
    "SkillLibrary",
    "attach_skills",
    "skills_dir",
]
