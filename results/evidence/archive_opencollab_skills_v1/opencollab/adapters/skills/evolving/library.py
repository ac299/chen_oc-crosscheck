"""On-disk skill library with versioned edits and a skill lifecycle.

Layout of a library directory::

    library.json             status, version and evidence of every skill
    evolution_log.jsonl      append-only record of every proposed and applied edit
    <name>/SKILL.md          current version, same format as FileSkillStore
    <name>/history/v<N>.md   every earlier version, kept for rollback and comparison

A skill moves ``trial -> active -> retired``. Only trial and active skills are
loaded into sessions. A directory without ``library.json`` is treated as a
hand-written library: every ``<name>/SKILL.md`` is loadable.

Sessions only read the library. Edits come from the evolution loop, which runs
between experiment runs, so a run always sees one fixed library state.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from opencollab.adapters.skills.file_skill_store import _parse_skill

LIBRARY_FILE = "library.json"
LOG_FILE = "evolution_log.jsonl"
STATUSES = ("trial", "active", "retired")
LOADABLE = frozenset({"trial", "active"})

# Library Drift (arXiv 2605.19576) and skill shadowing (2605.24050): an
# unbounded library degrades selection, so the number of loadable skills and
# the size of each one are capped.
MAX_LOADABLE_SKILLS = 5
MAX_BODY_CHARS = 2000
MAX_DESCRIPTION_CHARS = 300
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,47}$")


class LibraryError(ValueError):
    """An edit that would leave the library invalid."""


@dataclass
class SkillRecord:
    name: str
    status: str = "trial"
    version: int = 1
    evidence: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


def render_skill_md(name: str, description: str, body: str) -> str:
    # json.dumps yields a valid YAML scalar, so descriptions with colons stay intact.
    return f"---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n{body.strip()}\n"


class SkillLibrary:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)
        self._records: dict[str, SkillRecord] | None = self._read_records()

    # -- reading -----------------------------------------------------------

    @property
    def managed(self) -> bool:
        """Whether a ``library.json`` exists (as opposed to a hand-written folder)."""
        return self._records is not None

    def _read_records(self) -> dict[str, SkillRecord] | None:
        path = self.root / LIBRARY_FILE
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        records = {}
        for name, item in (raw.get("skills") or {}).items():
            if item.get("status") not in STATUSES:
                raise LibraryError(f"{path}: skill {name!r} has unknown status {item.get('status')!r}")
            records[name] = SkillRecord(name=name, **{k: v for k, v in item.items() if k != "name"})
        return records

    def records(self) -> dict[str, SkillRecord]:
        return dict(self._records or {})

    def loadable_names(self) -> list[str]:
        if self._records is None:
            if not self.root.is_dir():
                return []
            return sorted(p.name for p in self.root.iterdir() if (p / "SKILL.md").is_file())
        return sorted(n for n, r in self._records.items() if r.status in LOADABLE)

    def read(self, name: str) -> tuple[str, str]:
        """Return ``(description, body)`` of the current version."""
        parsed = _parse_skill((self.root / name / "SKILL.md").read_text(encoding="utf-8"))
        if parsed is None:
            raise LibraryError(f"skill {name!r} has a malformed SKILL.md")
        return parsed[1], parsed[2]

    # -- editing -----------------------------------------------------------

    def add(self, name: str, description: str, body: str, *, evidence: list[str], reason: str) -> SkillRecord:
        records = self._require_managed()
        if not _NAME_RE.match(name):
            raise LibraryError(f"invalid skill name {name!r}: use lowercase letters, digits and '-'")
        if name in records:
            raise LibraryError(f"skill {name!r} already exists; patch it instead")
        if len(self.loadable_names()) >= MAX_LOADABLE_SKILLS:
            raise LibraryError(f"library already holds {MAX_LOADABLE_SKILLS} loadable skills; retire one first")
        self._check_content(description, body)
        self._write_atomic(self.root / name / "SKILL.md", render_skill_md(name, description, body))
        record = SkillRecord(name=name, evidence=list(evidence))
        record.history.append(_event("add", reason, version=1))
        records[name] = record
        self._save()
        return record

    def patch(self, name: str, *, body: str, description: str | None = None,
              evidence: list[str], reason: str) -> SkillRecord:
        record = self._existing(name)
        if record.status == "retired":
            raise LibraryError(f"skill {name!r} is retired")
        old_description, _ = self.read(name)
        description = old_description if description is None else description
        self._check_content(description, body)
        history_dir = self.root / name / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.root / name / "SKILL.md", history_dir / f"v{record.version}.md")
        record.version += 1
        self._write_atomic(self.root / name / "SKILL.md", render_skill_md(name, description, body))
        record.evidence = sorted(set(record.evidence) | set(evidence))
        record.history.append(_event("patch", reason, version=record.version))
        self._save()
        return record

    def set_status(self, name: str, status: str, *, reason: str) -> SkillRecord:
        if status not in STATUSES:
            raise LibraryError(f"unknown status {status!r}")
        record = self._existing(name)
        if record.status == status:
            return record
        if status in LOADABLE and record.status not in LOADABLE and len(self.loadable_names()) >= MAX_LOADABLE_SKILLS:
            raise LibraryError(f"library already holds {MAX_LOADABLE_SKILLS} loadable skills")
        record.history.append(_event(f"status:{record.status}->{status}", reason, version=record.version))
        record.status = status
        self._save()
        return record

    def retire(self, name: str, *, reason: str) -> SkillRecord:
        return self.set_status(name, "retired", reason=reason)

    def rollback(self, name: str, *, reason: str) -> SkillRecord:
        """Restore the previous version, e.g. when a patch fails its gate."""
        record = self._existing(name)
        previous = self.root / name / "history" / f"v{record.version - 1}.md"
        if not previous.is_file():
            raise LibraryError(f"skill {name!r} has no earlier version")
        self._write_atomic(self.root / name / "SKILL.md", previous.read_text(encoding="utf-8"))
        previous.unlink()
        record.version -= 1
        record.history.append(_event("rollback", reason, version=record.version))
        self._save()
        return record

    def remove(self, name: str, *, reason: str) -> None:
        """Delete a trial skill that never passed its gate. Accepted skills are retired, never removed."""
        record = self._existing(name)
        if record.status != "trial" or record.version != 1:
            raise LibraryError(f"only an unpatched trial skill can be removed, {name!r} is {record.status}")
        shutil.rmtree(self.root / name)
        del self._require_managed()[name]
        self._save()
        self.log({"op": "remove", "skill": name, "reason": reason})

    def log(self, event: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / LOG_FILE).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"time": time.time(), **event}, ensure_ascii=False) + "\n")

    # -- whole-library operations -----------------------------------------

    @classmethod
    def create(cls, root: str | os.PathLike[str]) -> SkillLibrary:
        root = Path(root)
        if (root / LIBRARY_FILE).exists():
            raise LibraryError(f"{root} already holds a library")
        root.mkdir(parents=True, exist_ok=True)
        (root / LIBRARY_FILE).write_text(json.dumps({"skills": {}}, indent=1), encoding="utf-8")
        return cls(root)

    def snapshot(self, dest: str | os.PathLike[str]) -> Path:
        """Copy the loadable skills to ``dest`` so a batch of runs reads one frozen state."""
        dest = Path(dest)
        if dest.exists():
            raise LibraryError(f"snapshot destination {dest} already exists")
        dest.mkdir(parents=True)
        for name in self.loadable_names():
            (dest / name).mkdir()
            shutil.copyfile(self.root / name / "SKILL.md", dest / name / "SKILL.md")
        if self.managed:
            shutil.copyfile(self.root / LIBRARY_FILE, dest / LIBRARY_FILE)
        return dest

    # -- helpers -----------------------------------------------------------

    def _require_managed(self) -> dict[str, SkillRecord]:
        if self._records is None:
            raise LibraryError(f"{self.root} has no {LIBRARY_FILE}; create the library first")
        return self._records

    def _existing(self, name: str) -> SkillRecord:
        records = self._require_managed()
        if name not in records:
            raise LibraryError(f"unknown skill {name!r}")
        return records[name]

    @staticmethod
    def _check_content(description: str, body: str) -> None:
        if not description.strip() or not body.strip():
            raise LibraryError("description and body must be non-empty")
        if len(description) > MAX_DESCRIPTION_CHARS:
            raise LibraryError(f"description exceeds {MAX_DESCRIPTION_CHARS} characters")
        if len(body) > MAX_BODY_CHARS:
            raise LibraryError(f"body exceeds {MAX_BODY_CHARS} characters")
        if "\n---" in body or body.lstrip().startswith("---"):
            raise LibraryError("body must not contain a frontmatter delimiter line")

    def _save(self) -> None:
        records = self._require_managed()
        skills = {n: {k: v for k, v in asdict(r).items() if k != "name"} for n, r in sorted(records.items())}
        payload = {"skills": skills}
        self._write_atomic(self.root / LIBRARY_FILE, json.dumps(payload, ensure_ascii=False, indent=1))

    @staticmethod
    def _write_atomic(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)


def _event(op: str, reason: str, *, version: int) -> dict[str, Any]:
    return {"op": op, "reason": reason, "version": version, "time": time.time()}


__all__ = [
    "LOADABLE",
    "MAX_BODY_CHARS",
    "MAX_LOADABLE_SKILLS",
    "LibraryError",
    "SkillLibrary",
    "SkillRecord",
]
