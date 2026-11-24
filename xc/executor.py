"""Deterministic executor: build the test x candidate pass/fail matrix.

No LLM is involved here. Every cell is produced by running pytest on a fresh
copy of the base workspace with one candidate patch applied and one set of
test files added. This is the CodeT / TEX cross-execution idea, computed by
plain code so that it is reproducible and costs no tokens.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

PYTEST_TIMEOUT = 120


@dataclass
class TestOutcome:
    """Per-test-case results of one test file set on one code version."""

    cases: dict[str, str] = field(default_factory=dict)  # nodeid -> pass|fail|error
    messages: dict[str, str] = field(default_factory=dict)  # nodeid -> short failure text
    collect_error: str | None = None

    @property
    def passed(self) -> set[str]:
        return {k for k, v in self.cases.items() if v == "pass"}

    @property
    def failed(self) -> set[str]:
        return {k for k, v in self.cases.items() if v != "pass"}


def _run(cmd: list[str], cwd: Path, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def snapshot_base(workspace: Path, dest: Path) -> None:
    """Copy the committed base tree (HEAD) of the workspace into dest."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"], cwd=workspace, capture_output=True, check=True,
    )
    subprocess.run(["tar", "-xf", "-"], cwd=dest, input=archive.stdout, check=True)


def apply_patch(tree: Path, patch: str) -> str | None:
    """Apply a git diff to tree. Returns an error string or None."""
    if not patch or not patch.strip():
        return None
    _run(["git", "init", "-q"], tree)
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "--reject", "-"],
        cwd=tree, input=patch, capture_output=True, text=True,
    )
    shutil.rmtree(tree / ".git", ignore_errors=True)
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout)[-800:]
    return None


_TEST_PATH = re.compile(r"^\+\+\+ b/(.+)$", re.M)


def changed_paths(patch: str) -> list[str]:
    return sorted(set(_TEST_PATH.findall(patch or "")))


def test_paths(patch: str, prefix: str | None = None) -> list[str]:
    """Test files added or changed by a patch (optionally under prefix)."""
    out = []
    for p in changed_paths(patch):
        name = Path(p).name
        if prefix is not None and not p.startswith(prefix):
            continue
        if name.startswith("test_") and name.endswith(".py"):
            out.append(p)
    return out


def extract_files(patch: str, paths: list[str], base: Path) -> dict[str, str]:
    """Materialise selected files from a patch applied to the base tree."""
    if not paths:
        return {}
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "t"
        shutil.copytree(base, tree)
        err = apply_patch(tree, patch)
        files = {}
        for p in paths:
            f = tree / p
            if f.exists():
                files[p] = f.read_text(encoding="utf-8", errors="replace")
        if err and not files:
            return {}
        return files


def _parse_junit(xml_path: Path) -> TestOutcome:
    out = TestOutcome()
    if not xml_path.exists():
        out.collect_error = "no junit report"
        return out
    root = ET.parse(xml_path).getroot()
    for case in root.iter("testcase"):
        cls = case.get("classname", "")
        nodeid = f"{cls}::{case.get('name')}"
        status = "pass"
        msg = ""
        for tag in ("failure", "error"):
            el = case.find(tag)
            if el is not None:
                status = "fail" if tag == "failure" else "error"
                msg = (el.get("message") or el.text or "")[:400]
        if case.find("skipped") is not None:
            status, msg = "error", "skipped"
        out.cases[nodeid] = status
        if msg:
            out.messages[nodeid] = msg
    return out


def run_tests(base: Path, code_patch: str, test_files: dict[str, str]) -> TestOutcome:
    """Run test_files against base + code_patch. Test files override the patch."""
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "t"
        shutil.copytree(base, tree)
        err = apply_patch(tree, code_patch)
        for rel, text in test_files.items():
            f = tree / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
        report = Path(tmp) / "r.xml"
        targets = sorted(test_files)
        # Infrastructure adapter (not a design change): repository tasks bring their
        # own environment, named by XC_TEST_PYTHON; the tree and its src/ go on
        # PYTHONPATH so tests import the candidate's code, never an installed copy.
        python = os.environ.get("XC_TEST_PYTHON") or sys.executable
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(tree)] + ([str(tree / "src")] if (tree / "src").is_dir() else []))
        try:
            proc = subprocess.run(
                [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
                 f"--junitxml={report}", *targets],
                cwd=tree, capture_output=True, text=True, timeout=PYTEST_TIMEOUT, env=env,
            )
        except subprocess.TimeoutExpired:
            out = TestOutcome(collect_error="pytest timeout")
            return out
        out = _parse_junit(report)
        if not out.cases:
            out.collect_error = (proc.stdout + proc.stderr)[-800:] or "no tests collected"
        if err:
            out.messages["__patch__"] = err
        return out
