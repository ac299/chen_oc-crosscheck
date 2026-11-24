"""Spec gate (CrossCheck v3): verify an upstream contract before it reaches other roles.

Problem it addresses (IO2CodeBench, io_extra_trailingzeros crosscheck r1): the Spec
Analyst could not infer the rule from 8 examples and wrote 25 mutually exclusive
guesses as "requirements". Coder A tried to satisfy all of them, never wrote the
program and spent its whole budget. Checking only the contract's examples did not
catch this: every guess listed the task's true outputs and merely noted "does NOT
match". What was never checked was the rule itself.

The gate therefore checks rules by executing them:
  1. Every example the analyst extracts from the task must carry a quote that
     occurs verbatim (whitespace-normalised) in the task text; others are dropped.
  2. Every `given` requirement must quote the task the same way, or it is demoted
     to `hypothesis`.
  3. Every `derived` / `hypothesis` requirement may carry `check`, a Python lambda
     over one input. The harness runs it on every verified task example in a
     separate process. Only rules that reproduce all of them are kept as verified;
     rules contradicted by an example are reported as ruled out.
  4. Requirements without an executable check are passed on only as unverified
     ideas, never as requirements.
If nothing survives, downstream roles get the original task text only.

Pure stdlib; the execution step runs `python -I` in a subprocess with a timeout.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field

_WS = re.compile(r"\s+")
_QUOTES = str.maketrans({"`": "", "'": "", '"': ""})


def norm(text: str) -> str:
    return _WS.sub(" ", (text or "").translate(_QUOTES)).strip().lower()


def quoted(source: str, task: str) -> bool:
    s = norm(source)
    return len(s) >= 3 and s in norm(task)


def parse_literal(text: str):
    try:
        return True, ast.literal_eval(text.strip())
    except (ValueError, SyntaxError):
        return False, None


_RUNNER = r"""
import ast, json, sys
data = json.loads(sys.stdin.read())
def match(a, e):
    if isinstance(e, (list, tuple)) and isinstance(a, (list, tuple)):
        return len(a) == len(e) and all(match(x, y) for x, y in zip(a, e))
    if isinstance(e, dict) and isinstance(a, dict):
        return set(a) == set(e) and all(match(a[k], e[k]) for k in e)
    if isinstance(a, bool) or isinstance(e, bool):
        return isinstance(a, bool) and isinstance(e, bool) and a == e
    if isinstance(e, float) and isinstance(a, (int, float)):
        return abs(a - e) < 1e-6
    return a == e
out = []
for rule in data["rules"]:
    try:
        fn = eval(rule, {"__builtins__": __builtins__})
    except Exception as exc:
        out.append({"error": "compile: " + type(exc).__name__}); continue
    res = {"pass": 0, "fail": 0, "first_fail": None}
    for ex in data["examples"]:
        try:
            ok = match(fn(ast.literal_eval(ex["input"])), ast.literal_eval(ex["output"]))
        except Exception as exc:
            ok = False
        if ok:
            res["pass"] += 1
        else:
            res["fail"] += 1
            if res["first_fail"] is None:
                res["first_fail"] = ex["input"]
    out.append(res)
print(json.dumps(out))
"""


def run_checks(rules: list[str], examples: list[dict], timeout: float = 20.0) -> list[dict]:
    if not rules:
        return []
    try:
        proc = subprocess.run([sys.executable, "-I", "-c", _RUNNER],
                              input=json.dumps({"rules": rules, "examples": examples}),
                              capture_output=True, text=True, timeout=timeout)
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:  # noqa: BLE001 - a hung or crashing check verifies nothing
        return [{"error": f"runner: {type(exc).__name__}"} for _ in rules]


@dataclass
class GateResult:
    examples: list[dict] = field(default_factory=list)     # verified task examples
    given: list[dict] = field(default_factory=list)
    verified: list[dict] = field(default_factory=list)     # executable rules matching every example
    ruled_out: list[dict] = field(default_factory=list)    # executable rules an example contradicts
    unverified: list[dict] = field(default_factory=list)   # rules without a usable check
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.given or self.verified)

    def summary(self) -> dict:
        return {"examples": len(self.examples), "given": len(self.given), "verified": len(self.verified),
                "ruled_out": len(self.ruled_out), "unverified": len(self.unverified), "passed": self.passed,
                "notes": self.notes[:10]}


def gate(spec: dict | None, task: str) -> GateResult:
    res = GateResult()
    if not isinstance(spec, dict):
        res.notes.append("no spec")
        return res
    for ex in spec.get("task_examples") or []:
        ok_in, _ = parse_literal(ex.get("input", ""))
        ok_out, _ = parse_literal(ex.get("output", ""))
        if ok_in and ok_out and quoted(ex.get("source", ""), task):
            res.examples.append(ex)
        else:
            res.notes.append(f"dropped task example {ex.get('input', '')[:40]!r}: "
                             + ("quote not in task" if ok_in and ok_out else "not a literal"))
    pending = []
    for i, req in enumerate(spec.get("requirements") or []):
        item = dict(req, id=i + 1)
        kind = req.get("kind")
        if kind == "given":
            if quoted(req.get("source", ""), task):
                res.given.append(item)
                continue
            res.notes.append(f"r{i + 1}: quote not found in task; demoted to hypothesis")
        check = (req.get("check") or "").strip()
        if check.startswith("lambda") and res.examples:
            pending.append(item)
        else:
            res.unverified.append(item)
    outcomes = run_checks([p["check"] for p in pending], res.examples)
    for item, out in zip(pending, outcomes):
        item["gate"] = out
        if "error" in out:
            res.unverified.append(item)
        elif out["fail"] == 0 and out["pass"] == len(res.examples):
            res.verified.append(item)
        else:
            res.ruled_out.append(item)
    # Contract items are numbered r1..rN in contract order: the Test Designer names
    # tests test_r<id>_..., and coverage is computed over 1..N.
    for n, item in enumerate(res.given + res.verified, 1):
        item["id"] = n
    return res


def render(res: GateResult) -> str:
    """Contract text handed to coders and the Test Designer."""
    if not res.passed:
        lines = ["(No requirement survived verification. Work from the task text and its examples only.)"]
    else:
        lines = ["Requirements (each checked against the task):"]
        for r in res.given:
            lines.append(f"  r{r['id']}. {r.get('behavior', '')}  [stated in the task: \"{r.get('source', '')[:160]}\"]")
        for r in res.verified:
            lines.append(f"  r{r['id']}. {r.get('behavior', '')}  [inferred rule; reproduces all "
                         f"{len(res.examples)} task examples]")
    if res.ruled_out:
        lines.append("Rules already ruled out by the task's examples (do not implement these):")
        for r in res.ruled_out[:25]:
            lines.append(f"  - {r.get('behavior', '')[:140]}  (fails on input {r['gate'].get('first_fail')})")
    if res.unverified:
        lines.append("Unverified ideas (not requirements; may be wrong):")
        for r in res.unverified[:10]:
            lines.append(f"  - {r.get('behavior', '')[:140]}")
    return "\n".join(lines)
