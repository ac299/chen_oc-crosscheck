"""Evolving skill library, its store, and the session wiring behind OPENCOLLAB_SKILLS_DIR."""

from __future__ import annotations

import asyncio
import json

import pytest

from opencollab.adapters.skills.evolving import SKILLS_DIR_ENV, EvolvingSkillStore, LibraryError, SkillLibrary
from opencollab.adapters.skills.evolving.attach import attach_skills
from opencollab.adapters.skills.evolving.library import MAX_BODY_CHARS, MAX_LOADABLE_SKILLS
from opencollab.adapters.skills.file_skill_store import FileSkillStore
from opencollab.adapters.tools.bash import BashTool
from opencollab.bootstrap.container import build_skill_store
from opencollab.domain.agent import Agent


def _lib(tmp_path) -> SkillLibrary:
    return SkillLibrary.create(tmp_path / "lib")


def _add(lib: SkillLibrary, name: str = "check-inputs", body: str = "Read the inputs first.") -> None:
    lib.add(name, "When inputs are unclear.", body, evidence=["run-1"], reason="test")


# -- library -----------------------------------------------------------------


def test_add_writes_a_skill_file_the_upstream_parser_accepts(tmp_path):
    lib = _lib(tmp_path)
    lib.add("check-inputs", "When: inputs are unclear.", "Step one.", evidence=["r1"], reason="seen twice")

    store = FileSkillStore(lib.root)
    assert [m.name for m in store.list_manifests()] == ["check-inputs"]
    assert store.list_manifests()[0].description == "When: inputs are unclear."
    assert store.get_body("check-inputs") == "Step one."
    record = SkillLibrary(lib.root).records()["check-inputs"]
    assert (record.status, record.version, record.evidence) == ("trial", 1, ["r1"])


def test_patch_keeps_the_previous_version_and_rollback_restores_it(tmp_path):
    lib = _lib(tmp_path)
    _add(lib, body="v1 body")
    lib.patch("check-inputs", body="v2 body", evidence=["r2"], reason="refine")

    assert lib.read("check-inputs")[1] == "v2 body"
    assert (lib.root / "check-inputs" / "history" / "v1.md").is_file()
    assert lib.records()["check-inputs"].evidence == ["r2", "run-1"]

    lib.rollback("check-inputs", reason="gate failed")
    assert lib.read("check-inputs")[1] == "v1 body"
    assert lib.records()["check-inputs"].version == 1


def test_loadable_cap_and_retirement(tmp_path):
    lib = _lib(tmp_path)
    for i in range(MAX_LOADABLE_SKILLS):
        _add(lib, f"skill-{i}")
    with pytest.raises(LibraryError, match="retire one first"):
        _add(lib, "one-too-many")

    lib.retire("skill-0", reason="no benefit")
    _add(lib, "one-too-many")
    assert "skill-0" not in lib.loadable_names()
    with pytest.raises(LibraryError):
        lib.set_status("skill-0", "active", reason="revive")


@pytest.mark.parametrize(
    ("name", "body", "message"),
    [
        ("Bad Name", "x", "invalid skill name"),
        ("ok-name", "x" * (MAX_BODY_CHARS + 1), "body exceeds"),
        ("ok-name", "text\n---\nname: injected", "frontmatter"),
    ],
)
def test_invalid_edits_are_rejected(tmp_path, name, body, message):
    with pytest.raises(LibraryError, match=message):
        _lib(tmp_path).add(name, "d", body, evidence=[], reason="r")


def test_remove_only_drops_unpatched_trials(tmp_path):
    lib = _lib(tmp_path)
    _add(lib)
    lib.set_status("check-inputs", "active", reason="passed gate")
    with pytest.raises(LibraryError):
        lib.remove("check-inputs", reason="x")
    _add(lib, "fresh")
    lib.remove("fresh", reason="gate failed")
    assert not (lib.root / "fresh").exists()
    assert json.loads((lib.root / "library.json").read_text())["skills"].keys() == {"check-inputs"}


def test_snapshot_copies_only_loadable_skills(tmp_path):
    lib = _lib(tmp_path)
    _add(lib, "kept")
    _add(lib, "gone")
    lib.retire("gone", reason="r")
    snap = lib.snapshot(tmp_path / "snap")
    assert SkillLibrary(snap).loadable_names() == ["kept"]
    assert not (snap / "gone").exists()


# -- store -------------------------------------------------------------------


def test_store_skips_retired_skills(tmp_path):
    lib = _lib(tmp_path)
    _add(lib, "kept")
    _add(lib, "gone")
    lib.retire("gone", reason="r")
    store = EvolvingSkillStore(lib.root)
    assert [m.name for m in store.list_manifests()] == ["kept"]
    assert store.get_body("gone") is None


def test_store_reads_a_hand_written_folder_without_library_json(tmp_path):
    (tmp_path / "manual").mkdir()
    (tmp_path / "manual" / "SKILL.md").write_text("---\nname: manual\ndescription: d\n---\nbody\n")
    assert EvolvingSkillStore(tmp_path).get_body("manual") == "body"


def test_missing_directory_yields_an_empty_store(tmp_path):
    assert EvolvingSkillStore(tmp_path / "absent").list_manifests() == ()


def test_build_skill_store_prefers_the_configured_library(tmp_path, monkeypatch):
    lib = _lib(tmp_path)
    _add(lib)
    workspace = tmp_path / "ws"
    (workspace / "skills").mkdir(parents=True)
    monkeypatch.delenv(SKILLS_DIR_ENV, raising=False)
    assert build_skill_store(str(workspace)).list_manifests() == ()

    monkeypatch.setenv(SKILLS_DIR_ENV, str(lib.root))
    assert [m.name for m in build_skill_store(str(workspace)).list_manifests()] == ["check-inputs"]


# -- session wiring ----------------------------------------------------------


def _agent(tools=None) -> Agent:
    return Agent(name="coder", system_prompt="You write code.", tools=[BashTool()] if tools is None else tools)


def test_unset_variable_leaves_the_agent_untouched(monkeypatch):
    monkeypatch.delenv(SKILLS_DIR_ENV, raising=False)
    agent = _agent()
    seeds = [{"role": "system", "content": "x"}]
    assert attach_skills(agent, seeds) == (agent, seeds)


def test_empty_library_leaves_the_agent_untouched(tmp_path, monkeypatch):
    monkeypatch.setenv(SKILLS_DIR_ENV, str(_lib(tmp_path).root))
    agent = _agent()
    assert attach_skills(agent, None)[0] is agent


def test_tool_less_sessions_stay_tool_less(tmp_path, monkeypatch):
    lib = _lib(tmp_path)
    _add(lib)
    monkeypatch.setenv(SKILLS_DIR_ENV, str(lib.root))
    agent = _agent(tools=[])
    assert attach_skills(agent, None)[0] is agent


def test_attach_adds_use_skill_and_catalog_without_mutating_the_template(tmp_path, monkeypatch):
    lib = _lib(tmp_path)
    _add(lib)
    monkeypatch.setenv(SKILLS_DIR_ENV, str(lib.root))
    agent = _agent()
    seeds = [{"role": "system", "content": "identity"}]

    extended, new_seeds = attach_skills(agent, seeds)

    assert [t.name for t in extended.tools] == ["bash", "use_skill"]
    assert "- check-inputs: When inputs are unclear." in extended.system_prompt
    assert [t.name for t in agent.tools] == ["bash"] and agent.system_prompt == "You write code."
    assert seeds == [{"role": "system", "content": "identity"}]
    assert new_seeds[-1]["_ctx"]["layer"] == "skill" and "check-inputs" in new_seeds[-1]["content"]
    use_skill = extended.tools[-1]
    assert asyncio.run(use_skill.execute_with_runtime({"name": "check-inputs"}, None)) == "Read the inputs first."


def test_an_existing_use_skill_is_not_duplicated(tmp_path, monkeypatch):
    lib = _lib(tmp_path)
    _add(lib)
    monkeypatch.setenv(SKILLS_DIR_ENV, str(lib.root))
    from opencollab.adapters.tools.use_skill import UseSkillTool

    agent = _agent(tools=[BashTool(), UseSkillTool(EvolvingSkillStore(lib.root))])
    assert attach_skills(agent, None)[0] is agent


def test_build_session_wires_skills_for_any_session(tmp_path, monkeypatch):
    from opencollab.bootstrap.session_factory import build_session
    from tests.support.session_characterization_test_support import FakeLLMClient

    lib = _lib(tmp_path)
    _add(lib)
    monkeypatch.setenv(SKILLS_DIR_ENV, str(lib.root))
    session = build_session(agent=_agent(), llm=FakeLLMClient(), max_budget_tokens=1000)
    assert "use_skill" in [t.name for t in session.agent.tools]
    assert "## Skills" in session.state.messages[0]["content"]
