"""Offline tests for the v3 spec gate (no model calls)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xc import specgate as sg  # noqa: E402

TASK = """`program.py` must define `process(input_data)`.

Examples:
- `process([0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0])` returns `2`
- `process([0, 0, 1, 0, 1, 1, 0, 0, 1])` returns `0`
- `process([1, 0, 0, 1, 0, 0])` returns `2`
- `process([0, 1, 1, 1, 0, 1, 0])` returns `1`
- `process([0, 1, 1, 0, 0, 0, 0])` returns `4`
"""

EXAMPLES = [
    {"input": "[0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0]", "output": "2",
     "source": "`process([0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0])` returns `2`"},
    {"input": "[0, 0, 1, 0, 1, 1, 0, 0, 1]", "output": "0",
     "source": "`process([0, 0, 1, 0, 1, 1, 0, 0, 1])` returns `0`"},
    {"input": "[1, 0, 0, 1, 0, 0]", "output": "2", "source": "`process([1, 0, 0, 1, 0, 0])` returns `2`"},
    {"input": "[0, 1, 1, 1, 0, 1, 0]", "output": "1", "source": "`process([0, 1, 1, 1, 0, 1, 0])` returns `1`"},
    {"input": "[0, 1, 1, 0, 0, 0, 0]", "output": "4", "source": "`process([0, 1, 1, 0, 0, 0, 0])` returns `4`"},
]


def hyp(behavior, check):
    return {"kind": "hypothesis", "behavior": behavior, "source": "", "check": check}


def test_real_failure_pattern_is_ruled_out_and_the_true_rule_kept():
    # The v2.2 contract listed guesses like these as requirements.
    spec = {"api": "process(list) -> int", "task_examples": EXAMPLES, "ambiguities": [], "requirements": [
        hyp("count of zeros", "lambda x: x.count(0)"),
        hyp("count of ones", "lambda x: x.count(1)"),
        hyp("longest run of ones", "lambda x: max((len(r) for r in ''.join(map(str, x)).split('0')), default=0)"),
        hyp("number of trailing zeros", "lambda x: len(x) - len(''.join(map(str, x)).rstrip('0'))"),
    ]}
    res = sg.gate(spec, TASK)
    assert len(res.examples) == 5
    assert [r["behavior"] for r in res.verified] == ["number of trailing zeros"]
    assert len(res.ruled_out) == 3
    text = sg.render(res)
    assert "trailing zeros" in text and "ruled out" in text


def test_nothing_verified_falls_back_to_task_only():
    spec = {"api": "", "task_examples": EXAMPLES, "ambiguities": [], "requirements": [
        hyp("count of zeros", "lambda x: x.count(0)"),
        hyp("a rule without a check", ""),
    ]}
    res = sg.gate(spec, TASK)
    assert not res.passed
    text = sg.render(res)
    assert text.startswith("(No requirement survived verification")
    assert "Unverified ideas" in text


def test_invented_examples_and_unquoted_given_are_rejected():
    spec = {"api": "", "ambiguities": [],
            "task_examples": EXAMPLES[:2] + [{"input": "[1, 1]", "output": "9", "source": "process([1, 1]) is 9"}],
            "requirements": [
                {"kind": "given", "behavior": "defines process", "source": "must define `process(input_data)`", "check": ""},
                {"kind": "given", "behavior": "raises on empty", "source": "empty input raises ValueError", "check": ""},
            ]}
    res = sg.gate(spec, TASK)
    assert len(res.examples) == 2                      # the invented example has no quote in the task
    assert [r["behavior"] for r in res.given] == ["defines process"]
    assert [r["behavior"] for r in res.unverified] == ["raises on empty"]  # demoted, no check


def test_crashing_and_hanging_checks_verify_nothing():
    spec = {"api": "", "task_examples": EXAMPLES, "ambiguities": [], "requirements": [
        hyp("crash", "lambda x: 1 / 0"),
        hyp("not a lambda", "x.count(0)"),
        hyp("syntax", "lambda x: )"),
    ]}
    res = sg.gate(spec, TASK)
    assert not res.verified
    assert len(res.ruled_out) + len(res.unverified) == 3


def test_ids_follow_contract_order():
    spec = {"api": "", "task_examples": EXAMPLES, "ambiguities": [], "requirements": [
        hyp("count of zeros", "lambda x: x.count(0)"),
        {"kind": "given", "behavior": "defines process", "source": "must define `process(input_data)`", "check": ""},
        hyp("number of trailing zeros", "lambda x: len(x) - len(''.join(map(str, x)).rstrip('0'))"),
    ]}
    res = sg.gate(spec, TASK)
    assert [r["id"] for r in res.given + res.verified] == [1, 2]
