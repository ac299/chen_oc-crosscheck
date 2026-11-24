"""Evolution steps of adapters.skills.evolving: evidence, reflection, screening, gate, lifecycle."""

from __future__ import annotations

import asyncio
import json

from opencollab.adapters.skills.evolving import SkillLibrary
from opencollab.adapters.skills.evolving.evidence import RunOutcome, skills_used
from opencollab.adapters.skills.evolving.gate import decide, sign_test
from opencollab.adapters.skills.evolving.lifecycle import nominate
from opencollab.adapters.skills.evolving.reflector import (
    Edit,
    apply_edit,
    build_prompt,
    parse_edits,
    propose,
    revert_edit,
)
from opencollab.adapters.skills.evolving.screen import screen, task_specific_hits, term_index

BODY = "## When to use\nInputs are unclear.\n## Steps\nRead the docstring.\nCheck examples.\n## Pitfalls\nGuessing."


def _lib(tmp_path) -> SkillLibrary:
    lib = SkillLibrary.create(tmp_path / "lib")
    lib.add("check-inputs", "When inputs are unclear.", BODY, evidence=["r0"], reason="seed")
    return lib


def _reply(*edits) -> str:
    return "Here you go:\n```json\n" + json.dumps({"analysis": "a", "edits": list(edits)}) + "\n```"


def _ask(reply: str):
    prompts: list[str] = []

    async def ask(prompt: str) -> str:
        prompts.append(prompt)
        return reply

    return ask, prompts


# -- evidence ----------------------------------------------------------------


def test_skills_used_reads_successful_use_skill_calls(tmp_path):
    path = tmp_path / "trajectory.jsonl"
    records = [
        {"type": "tool_exec", "payload": {"tool": "bash", "args": {"command": "ls"}, "result": ""}},
        {"type": "tool_exec", "payload": {"tool": "use_skill", "args": {"name": "a"}, "result": "body"}},
        {"type": "tool_exec", "payload": {"tool": "use_skill", "args": {"name": "x"}, "result": "Unknown skill 'x'."}},
        {"type": "llm_call", "payload": {}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in records) + "\nnot json\n")
    assert skills_used(path) == ("a",)
    assert skills_used(tmp_path / "missing.jsonl") == ()


# -- gate --------------------------------------------------------------------


def _runs(results: str) -> list[RunOutcome]:
    return [RunOutcome(task=f"t{i}", rep=0, resolved=c == "1") for i, c in enumerate(results)]


def test_gate_counts_only_discordant_pairs_and_rejects_ties():
    accepted = decide(_runs("0011"), _runs("1011"))
    assert (accepted.accept, accepted.wins, accepted.losses, accepted.pairs) == (True, 1, 0, 4)
    assert not decide(_runs("0011"), _runs("1001")).accept
    assert not decide(_runs("0011"), _runs("0011")).accept


def test_sign_test():
    assert sign_test(0, 0) == 1.0
    assert abs(sign_test(10, 0) - 2 / 1024) < 1e-12
    assert sign_test(3, 3) == 1.0


# -- reflector ---------------------------------------------------------------


def test_prompt_shows_library_runs_and_guide(tmp_path):
    lib = _lib(tmp_path)
    outcome = RunOutcome("t1", 0, False, run_id="run-a", skills_used=("check-inputs",), details={"task": "Do X"})
    prompt = build_prompt(lib, [outcome])
    assert "## check-inputs (trial, loaded in 1 runs)" in prompt
    assert "run run-a | task t1 | rep 0 | FAILED | skills loaded: check-inputs" in prompt
    assert "Never name a specific task's functions" in prompt


def test_parse_edits_filters_inapplicable_edits(tmp_path):
    lib = _lib(tmp_path)
    reply = _reply(
        {"op": "add", "skill": "new-skill", "description": "d", "body": "b", "reason": "r", "evidence": ["x"]},
        {"op": "add", "skill": "check-inputs", "description": "d", "body": "b"},
        {"op": "patch", "skill": "check-inputs", "body": "entirely new text"},
        {"op": "retire", "skill": "absent"},
        {"op": "explode", "skill": "check-inputs"},
    )
    edits, problems = parse_edits(reply, lib, max_edits=5)
    assert [e.skill for e in edits] == ["new-skill"]
    assert any("already exists" in p for p in problems)
    assert any("rewrites the skill" in p for p in problems)
    assert any("no such loadable skill" in p for p in problems)
    assert any("bad op" in p for p in problems)
    assert parse_edits("no json at all", lib) == ([], ["reply contains no JSON object"])


def test_parse_edits_caps_the_number_of_edits(tmp_path):
    lib = _lib(tmp_path)
    many = [{"op": "add", "skill": f"s-{i}", "description": "d", "body": "b"} for i in range(4)]
    edits, _ = parse_edits(_reply(*many), lib, max_edits=2)
    assert len(edits) == 2


def test_an_incremental_patch_is_accepted(tmp_path):
    lib = _lib(tmp_path)
    reply = _reply({"op": "patch", "skill": "check-inputs", "body": BODY + "\nAlso read the tests.", "reason": "r"})
    edits, problems = parse_edits(reply, lib)
    assert problems == [] and edits[0].op == "patch"


def test_apply_and_revert_each_op(tmp_path):
    lib = _lib(tmp_path)
    add = Edit("add", "new-skill", "r", (), body="b", description="d")
    prior = apply_edit(lib, add)
    assert "new-skill" in lib.loadable_names()
    revert_edit(lib, add, prior, reason="gate")
    assert "new-skill" not in lib.records()

    patch = Edit("patch", "check-inputs", "r", (), body=BODY + "\nmore")
    prior = apply_edit(lib, patch)
    revert_edit(lib, patch, prior, reason="gate")
    assert lib.read("check-inputs")[1] == BODY

    retire = Edit("retire", "check-inputs", "r", ())
    prior = apply_edit(lib, retire)
    assert lib.loadable_names() == []
    revert_edit(lib, retire, prior, reason="gate")
    assert lib.records()["check-inputs"].status == "trial"


def test_tried_edits_are_shown_with_a_rule_not_to_repeat_them(tmp_path):
    from opencollab.adapters.skills.evolving.reflector import TriedEdit

    lib = _lib(tmp_path)
    plain = build_prompt(lib, [])
    assert "Edits already tried" not in plain
    tried = TriedEdit("add", "infer-contracts", "d", "Return the stated type.", "rejected by gate", "3 wins, 6 losses")
    prompt = build_prompt(lib, [], tried=[tried])
    assert "## add infer-contracts: rejected by gate\nreason: 3 wins, 6 losses" in prompt
    assert "Do not\npropose them again" in prompt
    assert prompt.index("# Edits already tried") < prompt.index("# Runs")


def test_propose_calls_the_injected_model(tmp_path):
    lib = _lib(tmp_path)
    ask, prompts = _ask(_reply({"op": "retire", "skill": "check-inputs", "reason": "unused"}))
    edits, problems, raw = asyncio.run(propose(ask, lib, []))
    assert [e.op for e in edits] == ["retire"] and problems == [] and len(prompts) == 1


# -- screen ------------------------------------------------------------------


TASKS = {
    "t1": "Write `task_func` that reads column 'closing_price' from prices.csv.",
    "t2": "Write `task_func` that returns the mean of a list.",
    "t3": "Write `task_func` using `max_depth` for a tree.",
    "t4": "Write `task_func` that sorts strings.",
}


def test_rule_check_flags_terms_from_few_tasks_only():
    index = term_index(TASKS)
    leaky = Edit("add", "price-columns", "r", (), body="Read the closing_price column from prices.csv.",
                 description="d")
    generic = Edit("add", "unclear-columns", "r", (), body="Implement task_func; do not guess column names.",
                   description="d")
    hits = task_specific_hits(leaky, index, n_tasks=len(TASKS))
    assert any(h.startswith("closing_price") for h in hits) and any(h.startswith("prices.csv") for h in hits)
    assert task_specific_hits(generic, index, n_tasks=len(TASKS)) == []


def test_plain_words_are_left_to_the_judge():
    index = term_index({"t1": "Return the 'content' of each 'archive' with its 'date'.", "t2": "x", "t3": "y",
                        "t4": "z"})
    prose = Edit("add", "s", "r", (), body="Check the date format and the archive content.", description="d")
    assert task_specific_hits(prose, index, n_tasks=4) == []


def test_screen_runs_the_judge_only_after_the_rule_check():
    index = term_index(TASKS)
    ask, prompts = _ask('{"verdict": "general", "reason": "fine"}')
    leaky = Edit("add", "s", "r", (), body="Use max_depth=3.", description="d")
    result = asyncio.run(screen(leaky, ask=ask, index=index, n_tasks=4))
    assert not result.passed and prompts == []

    generic = Edit("add", "s", "r", (), body="State assumptions before coding.", description="d")
    assert asyncio.run(screen(generic, ask=ask, index=index, n_tasks=4)).passed

    rejecting, _ = _ask("not json")
    result = asyncio.run(screen(generic, ask=rejecting, index=index, n_tasks=4))
    assert not result.passed and result.verdict == "task_specific"


# -- lifecycle ---------------------------------------------------------------


def test_nominate_promotes_used_trials_and_flags_weak_active_skills(tmp_path):
    lib = _lib(tmp_path)
    lib.add("weak", "d", "b", evidence=[], reason="r")
    lib.set_status("weak", "active", reason="r")
    outcomes = [
        RunOutcome("t1", 0, False, skills_used=("weak", "check-inputs")),
        RunOutcome("t2", 0, False, skills_used=("weak",)),
        RunOutcome("t3", 0, False, skills_used=("weak",)),
        RunOutcome("t4", 0, True),
    ]
    actions = {(n.action, n.skill) for n in nominate(lib, outcomes)}
    assert actions == {("promote", "check-inputs"), ("ablate", "weak")}
