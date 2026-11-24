"""CrossCheck v2: cost-ordered escalation over frozen, audited, cross-validated evidence.

Roles (each an isolated OpenCollab session; handoffs are fixed by this code):
  Spec Analyst   read-only; writes the shared contract every role receives
  Coder A        implements in its own candidate worktree
  Test Designer  writes tests from the task only, in its own worktree; frozen
  Test Auditor   read-only; judges failing tests against the task, never sees code
  Repairer       revises a candidate from frozen failing evidence
  Coder B        independent second implementation, blind to A
  Arbiter        read-only; asked in both A/B orders, only for behavioral ties
  harness        plain code: freezes tests, builds the pass/fail matrix, decides

Escalation ladder, cheapest first (stop as soon as the evidence is sufficient):
  L1 verify    run the frozen suite on A                         ~0 tokens
  L2 audit     drop tests the Auditor finds unsupported by task  ~0.05 T
  L3 repair    one repair round of A on the remaining failures   ~0.5 T
  L4 diversify Coder B + cross matrix + one repair of B + select ~1.5 T

Variants for ablation (args["variant"]):
  full      the ladder above
  always    disable every early stop (fixed pipeline, all levels run)
  selftest  no Test Designer: evidence is A's own tests (coupled condition)
  noaudit   skip L2
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from opencollab import workflow  # noqa: E402
from opencollab.tools import builtin_tools  # noqa: E402

from xc import analysis as an  # noqa: E402
from xc import executor as ex  # noqa: E402
import contextvars  # noqa: E402

from xc import prompts as _P22  # noqa: E402
from xc import prompts_v4 as _P4  # noqa: E402

# The role prompts in use for the current run: v2.2/v3 prompts by default, the
# Single2-aware v4 prompts when variant starts with "v4". Context-local, so
# concurrent role sessions of one run all see the same set.
_PROMPTS: contextvars.ContextVar = contextvars.ContextVar("xc_prompts", default=_P22)


class _PromptProxy:
    def __getattr__(self, name):
        return getattr(_PROMPTS.get(), name)


P = _PromptProxy()
from xc import specgate  # noqa: E402
from xc.tools import LoadStartingPoint  # noqa: E402

INDEP_DIR = "xc_tests/"

# Per-role token caps. Without them coder A and the Test Designer drained the
# shared budget and later roles started with ~5k tokens (v0 runs).
BUDGET = {"spec": 60_000, "coder": 220_000, "tester": 150_000, "repair": 100_000,
          "auditor": 80_000, "arbiter": 30_000}

# v5 / v22b: role budgets as shares of the run budget still remaining when the role
# starts. The fixed caps above were tuned on single-file tasks; on repository tasks
# (EvoCodeBench) every CrossCheck role hit its cap while Duo's coders, which share
# the run budget, did not. The run total stays the same for every method (800k);
# the shares only stop an early role from leaving nothing for later ones.
BUDGET_SHARE = {"spec": 0.10, "coder_a": 0.45, "tester": 0.30, "auditor": 0.15,
                "repair_a": 0.35, "coder_b": 0.55, "repair_b": 0.50, "arbiter": 0.10}
_SCALED: contextvars.ContextVar = contextvars.ContextVar("xc_scaled_budget", default=None)


# v7 fast path: fixed caps for the fast solver and the Test Designer; every other
# role (the slow path) uses the scaled shares above.
_FIXED: contextvars.ContextVar = contextvars.ContextVar("xc_fixed_budget", default={})


def _budget(role: str) -> int | None:
    fixed = _FIXED.get()
    if role in fixed:
        return fixed[role]
    ctx = _SCALED.get()
    if ctx is None:
        base = {"coder_a": "coder", "coder_b": "coder", "repair_a": "repair", "repair_b": "repair"}.get(role, role)
        return BUDGET[base]
    remaining = ctx.tokens_remaining()
    if remaining == float("inf"):
        return None
    return max(20_000, int(BUDGET_SHARE[role] * remaining))

SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "api": {"type": "string"},
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "behavior": {"type": "string"},
                    "examples": {"type": "array", "items": {"type": "string"}},
                    "source": {"type": "string"},
                },
                "required": ["id", "behavior", "examples", "source"],
                "additionalProperties": False,
            },
        },
        "ambiguities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["api", "requirements", "ambiguities"],
    "additionalProperties": False,
}

SPEC_SCHEMA_V3 = {
    "type": "object",
    "properties": {
        "api": {"type": "string"},
        "task_examples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"input": {"type": "string"}, "output": {"type": "string"},
                               "source": {"type": "string"}},
                "required": ["input", "output", "source"],
                "additionalProperties": False,
            },
        },
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["given", "derived", "hypothesis"]},
                    "behavior": {"type": "string"},
                    "source": {"type": "string"},
                    "check": {"type": "string"},
                },
                "required": ["kind", "behavior", "source", "check"],
                "additionalProperties": False,
            },
        },
        "ambiguities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["api", "task_examples", "requirements", "ambiguities"],
    "additionalProperties": False,
}

AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"test": {"type": "string"}, "valid": {"type": "boolean"},
                               "reason": {"type": "string"}},
                "required": ["test", "valid", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verdicts"],
    "additionalProperties": False,
}

ARBITER_SCHEMA = {
    "type": "object",
    "properties": {"winner": {"type": "string", "enum": ["X", "Y"]}, "reason": {"type": "string"}},
    "required": ["winner", "reason"],
    "additionalProperties": False,
}


# ----------------------------------------------------------------- helpers

def _render_contract(spec: Any) -> tuple[str, int]:
    if not isinstance(spec, dict) or not spec.get("requirements"):
        return "(no contract available; rely on the task text)", 0
    lines = [f"API: {spec.get('api', '')}", "Requirements:"]
    for i, req in enumerate(spec["requirements"], 1):
        lines.append(f"  r{i}. {req.get('behavior', '')}  Examples: {'; '.join(req.get('examples') or [])}")
    lines += [f"Ambiguity: {a}" for a in spec.get("ambiguities") or []]
    return "\n".join(lines), len(spec["requirements"])


def _coder_tools(unisolated: bool) -> list[Any]:
    return list(builtin_tools("bash", "file_read", "file_write", "apply_patch", "grep", "git_diff",
                              headless=not unisolated))


class _Ledger:
    """Per-stage token and wall-clock accounting, plus which roles ran."""

    def __init__(self, ctx: Any) -> None:
        self.ctx, self.rows, self._t, self._k = ctx, [], time.time(), ctx.tokens_spent()

    def mark(self, stage: str) -> None:
        now, k = time.time(), self.ctx.tokens_spent()
        self.rows.append({"stage": stage, "tokens": k - self._k, "seconds": round(now - self._t, 1)})
        self._t, self._k = now, k


def _own_tests(cand: Any, base: Path) -> dict[str, str]:
    paths = [p for p in ex.test_paths(cand.diff) if not p.startswith(INDEP_DIR)]
    return ex.extract_files(cand.diff, paths, base)


def _test_source(files: dict[str, str], nodeid: str) -> str:
    """Source of one test function (best effort), for the Auditor and Repairer."""
    name = nodeid.split("::")[-1].split("[")[0]
    for text in files.values():
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.lstrip().startswith(f"def {name}("):
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j].startswith((" ", "\t"))):
                    j += 1
                k = i
                while k > 0 and lines[k - 1].lstrip().startswith("@"):
                    k -= 1
                return "\n".join(lines[k:j]).strip()
    return "(source not found)"


def _last_json(text: Any) -> dict | None:
    """Parse the last top-level JSON object in a role's final message."""
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        return None
    decoder = json.JSONDecoder()
    best = None
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
            except ValueError:
                continue
            if isinstance(obj, dict) and "verdicts" in obj:
                best = obj
    return best


async def _with_retry(make, ok) -> Any:
    """Run a role; retry once with a note if the result is unusable (provider cut-off)."""
    res = await make("")
    if ok(res):
        return res, 0
    res2 = await make(P.RETRY_NOTE)
    return (res2 if ok(res2) else res), 1


# ----------------------------------------------------------------- role calls

async def _audit(ctx: Any, goal: str, failing: list[str], outcome: ex.TestOutcome,
                 files: dict[str, str]) -> dict[str, dict]:
    """Ask the Auditor whether each failing independent test follows from the task."""
    if not failing:
        return {}
    blocks = []
    for k in failing[:25]:
        blocks.append(f"### {k}\nobserved failure: {outcome.messages.get(k, '')[:300]}\n"
                      f"```python\n{_test_source(files, k)[:1500]}\n```")
    # v2.1: the auditor runs as an isolated candidate (base code only, no
    # implementation) with a shell, because in t4_allocate r10 it judged two wrong
    # tests "valid" after doing big-integer arithmetic in its head. Its diff is
    # discarded; only the JSON verdicts in its final message are used.
    run = await ctx.candidate_agent(
        P.AUDITOR_PROMPT.format(goal=goal, cases="\n".join(blocks), workspace_rule=P.WORKSPACE_RULE),
        label="test-auditor", tools=list(builtin_tools("bash", "file_read", "grep", headless=False)),
        budget=_budget("auditor"))
    res = _last_json(run.output if run is not None else None)
    verdicts = {}
    for v in res.get("verdicts", []) if isinstance(res, dict) else []:
        name = str(v.get("test", ""))
        match = next((k for k in failing if k == name or k.endswith("::" + name) or name.endswith(k.split("::")[-1])), None)
        if match:
            verdicts[match] = {"valid": bool(v.get("valid")), "reason": str(v.get("reason", ""))[:300]}
    return verdicts


async def _repair(ctx: Any, *, who: str, goal: str, contract: str, cand: Any, base: Path,
                  indep: dict[str, str], failing: list[str], msgs: dict[str, str],
                  peer: list[str], own_fail: list[str], contested: list[str], unisolated: bool) -> Any:
    parts = []
    if failing:
        parts.append("Failing independent tests (frozen Test Designer suite):")
        for k in failing[:25]:
            parts.append(f"### {k}\nobserved: {msgs.get(k, '')[:300]}\n```python\n{_test_source(indep, k)[:1200]}\n```")
    if peer:
        parts.append("Failing tests written by the other implementer (they pass on that implementation):")
        parts += [f"  - {k}" for k in peer[:20]]
    if own_fail:
        parts.append("Your own tests that fail:")
        parts += [f"  - {k}" for k in own_fail[:20]]
    note = ""
    if contested:
        note = ("Contested tests (the evidence suggests these tests themselves may be wrong; "
                "re-read the task before changing behavior for them): " + ", ".join(contested[:20]))
    prompt = P.REPAIR_PROMPT.format(who=who, goal=goal, contract=contract,
                                    evidence="\n".join(parts) or "(no failing evidence)",
                                    contested=note, workspace_rule=P.WORKSPACE_RULE)
    tools = _coder_tools(unisolated) + [LoadStartingPoint(cand.diff)]
    return await ctx.candidate_agent(prompt, label=f"repair-{who.split()[-1]}", tools=tools,
                                     budget=_budget("repair_b" if who.endswith("B") else "repair_a"))


async def _arbitrate(ctx: Any, goal: str, a: str, b: str, dis: list, indep: dict[str, str]) -> str | None:
    """Ask twice with swapped labels; accept a winner only if both answers agree.

    Duo's adjudicator defaults to B on a tie, a fixed positional rule. Asking in
    both orders and requiring agreement cancels position bias by construction.
    """
    votes = []
    for first, second in ((a, b), (b, a)):
        lines = []
        for source, case, va, vb in dis[:12]:
            x_out, y_out = (va, vb) if first == a else (vb, va)
            src = _test_source(indep, case) if source == "indep" else ""
            lines.append(f"- [{source}] {case}: X={x_out} Y={y_out}\n{src[:800]}")
        res = await ctx.agent(P.ARBITER_PROMPT.format(goal=goal, cases="\n".join(lines)),
                              schema=ARBITER_SCHEMA, label=f"arbiter-{first}-first", tools=[],
                              budget=_budget("arbiter"))
        pick = res.get("winner") if isinstance(res, dict) else None
        votes.append(first if pick == "X" else second if pick == "Y" else None)
    return votes[0] if votes[0] is not None and votes[0] == votes[1] else None


# ----------------------------------------------------------------- workflow

@workflow(
    name="crosscheck",
    description="Cost-ordered escalation: frozen independent tests, audit, repair, then a blind second coder",
    phases=["spec", "verify", "audit", "repair", "diversify", "select"],
)
async def crosscheck(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    goal = str(args.get("goal") or "").strip()
    if not goal:
        return {"status": "error", "error": "missing goal"}
    raw_variant = str(args.get("variant") or "full")
    # "v3" or "v3-<ablation>" selects v3 (spec gate + escalate on an empty A);
    # anything else runs v2.2 unchanged.
    v3 = raw_variant.startswith("v3")
    # v4: v2.2 logic + Single2-aware prompts. v5: v4 + scaled role budgets.
    # v22b: v2.2 prompts + scaled role budgets.
    # v7: fast path (a Single2-like fast solver, task only, 150k cap, with an
    # independent 80k Test Designer); slow path = v6 with the Spec Analyst run only
    # when the slow path needs a contract for Coder B.
    v7 = raw_variant.startswith("v7")
    # v6: v5 + escalate to the blind Coder B when Coder A produces no change (the v3 fix).
    v6 = raw_variant.startswith("v6") or v7
    v5, v22b = raw_variant.startswith("v5") or v6, raw_variant.startswith("v22b")
    v4 = raw_variant.startswith("v4") or v5
    head = raw_variant.split("-", 1)
    variant = head[1] if len(head) == 2 and head[0] in ("v3", "v4", "v5", "v6", "v7", "v22b") else (
        "full" if (v3 or v4 or v22b) else raw_variant)
    early_stop = variant != "always"
    version = "v3" if v3 else "v7" if v7 else "v6" if v6 else "v5" if v5 else "v4" if v4 else "v2.2b" if v22b else "v2.2"
    escalate_empty = v3 or v6
    _PROMPTS.set(_P4 if v4 else _P22)
    _SCALED.set(ctx if (v5 or v22b) else None)
    _FIXED.set({"coder_a": 150_000, "tester": 80_000} if v7 else {})
    unisolated = args.get("allow_unisolated_shell") is True
    ledger = _Ledger(ctx)
    rep: dict[str, Any] = {"variant": variant, "version": version, "retries": {}}
    tmp = tempfile.TemporaryDirectory(prefix="xc-base-")
    base = Path(tmp.name) / "base"
    ex.snapshot_base(Path(ctx.host_workspace), base)

    async def finish(cand: Any, level: int, winner: str, reason: str) -> dict[str, Any]:
        await ctx.adopt_candidate(cand)
        rep.update(level=level, winner=winner, reason=reason)
        ledger.mark("adopt")
        tmp.cleanup()
        return {"status": "completed", "report": json.loads(json.dumps(rep, default=str)), "ledger": ledger.rows}

    # ---- L0 shared contract
    await ctx.phase("spec")

    async def run_spec(note: str) -> Any:
        return await ctx.agent(P.SPEC_PROMPT.format(goal=goal) + note, schema=SPEC_SCHEMA, label="spec",
                               tools=list(builtin_tools("file_read", "grep")), budget=_budget("spec"))

    async def run_spec_v3(note: str) -> Any:
        return await ctx.agent(P.SPEC_PROMPT_V3.format(goal=goal) + note, schema=SPEC_SCHEMA_V3, label="spec",
                               tools=list(builtin_tools("file_read", "grep")), budget=_budget("spec"))

    if v7:
        contract, n_req = P.NO_CONTRACT, 0  # the Spec Analyst runs only on the slow path
        rep["retries"]["spec"] = None
    elif v3:
        spec, rep["retries"]["spec"] = await _with_retry(run_spec_v3, lambda s: isinstance(s, dict))
        gated = specgate.gate(spec, goal)
        contract = specgate.render(gated)
        n_req = len(gated.given) + len(gated.verified)
        rep["gate"] = gated.summary()
        rep["spec_v3"] = spec
    else:
        spec, rep["retries"]["spec"] = await _with_retry(run_spec, lambda s: isinstance(s, dict) and s.get("requirements"))
        contract, n_req = _render_contract(spec)
    rep["requirements"] = n_req
    ledger.mark("spec")

    # ---- L1 Coder A || Test Designer, then verify
    await ctx.phase("verify")

    def coder(who: str, style: str, label: str):
        async def make(note: str) -> Any:
            if v7 and label == "coder-a":
                text = P.FAST_PROMPT.format(goal=goal)
            else:
                text = P.CODER_PROMPT.format(who=who, goal=goal, contract=contract, style=style,
                                             workspace_rule=P.WORKSPACE_RULE)
            return await ctx.candidate_agent(
                text + note,
                label=label, tools=_coder_tools(unisolated),
                budget=_budget("coder_b" if label == "coder-b" else "coder_a"))
        return make

    # Optional two-layer experience memory for the Test Designer only (args
    # "td_memory" = memory directory, "td_memory_layers"); needs the memory module of
    # vendor/OpenCollab-skills2. Without "td_memory" the prompt is unchanged.
    td_memory = ""
    if args.get("td_memory"):
        from opencollab.adapters.memory import ExperienceMemory

        layers = tuple(args.get("td_memory_layers") or ("insights", "examples"))
        td_memory = ExperienceMemory.load(str(args["td_memory"])).render(goal, layers)
        rep["td_memory"] = {"layers": list(layers), "chars": len(td_memory)}

    async def make_tester(note: str) -> Any:
        return await ctx.candidate_agent(
            P.TESTER_PROMPT.format(goal=goal, contract=contract, workspace_rule=P.WORKSPACE_RULE)
            + (f"\n\n{td_memory}" if td_memory else "") + note,
            label="test-designer", tools=_coder_tools(unisolated), budget=_budget("tester"))

    has_diff = lambda c: c is not None and bool(c.diff.strip())  # noqa: E731
    has_tests = lambda c: c is not None and bool(ex.test_paths(c.diff, INDEP_DIR))  # noqa: E731
    jobs = [lambda: _with_retry(coder("implementer A", P.STYLE_A, "coder-a"), has_diff)]
    if variant != "selftest":
        jobs.append(lambda: _with_retry(make_tester, has_tests))
    results = await ctx.parallel(jobs)
    cand_a, rep["retries"]["coder_a"] = results[0] if results[0] else (None, 1)
    tdesign = None
    if variant != "selftest" and results[1]:
        tdesign, rep["retries"]["tester"] = results[1]
    ledger.mark("L1-generate")
    a_empty = not has_diff(cand_a)
    if a_empty and not escalate_empty:
        tmp.cleanup()
        return {"status": "error", "error": "coder A produced no change", "report": rep, "ledger": ledger.rows}
    if a_empty:
        rep["a_empty"] = True  # v3/v6: escalate straight to the blind Coder B instead of ending the run

    indep: dict[str, str] = {}
    if tdesign is not None:
        indep = ex.extract_files(tdesign.diff, ex.test_paths(tdesign.diff, INDEP_DIR), base)
    base_run = ex.run_tests(base, "", indep) if indep else ex.TestOutcome(collect_error="no tests")
    quality = an.suite_quality(base_run.cases, n_req, base_run.collect_error)
    if not quality.usable:
        indep = {}
    rep["suite"] = {**quality.__dict__, "coverage": round(quality.coverage, 2), "credible": quality.credible_for_stop()}
    rep["indep_files"] = indep  # kept for offline Base-to-Gold scoring by the grader

    invalid: set[str] = set()
    own_a: dict[str, str] = {}
    cand_a_best, a_label = (None, None) if a_empty else (cand_a, "A")
    if not a_empty:
        own_a = _own_tests(cand_a, base)
        run_a = ex.run_tests(base, cand_a.diff, indep) if indep else ex.TestOutcome()
        own_run_a = ex.run_tests(base, cand_a.diff, own_a) if own_a else ex.TestOutcome()
        fail_a = sorted(run_a.failed)
        rep["L1"] = {"indep_pass": len(run_a.passed), "indep_total": len(run_a.cases),
                     "own_pass": len(own_run_a.passed), "own_total": len(own_run_a.cases)}
        ledger.mark("L1-verify")

        if variant == "selftest":
            evidence_ok = len(own_run_a.cases) > 0 and not own_run_a.failed
        else:
            evidence_ok = quality.credible_for_stop() and not fail_a and not own_run_a.failed
        if evidence_ok and early_stop:
            return await finish(cand_a, 1, "A", "verified")

        # ---- L2 audit the failing independent tests (never shows A's code)
        invalid: set[str] = set()
        if indep and fail_a and variant not in ("noaudit", "selftest"):
            await ctx.phase("audit")
            verdicts = await _audit(ctx, goal, fail_a, run_a, indep)
            invalid = {k for k, v in verdicts.items() if not v["valid"]}
            rep["audit"] = verdicts
            ledger.mark("L2-audit")
            remaining_fail = [k for k in fail_a if k not in invalid]
            kept = len(run_a.cases) - len(invalid)
            still_credible = quality.usable and kept >= 4
            if not remaining_fail and not own_run_a.failed and still_credible and early_stop:
                return await finish(cand_a, 2, "A", "audited")
        fail_a_valid = [k for k in fail_a if k not in invalid]

        # ---- L3 repair A once on frozen, audited evidence
        cand_a_best, a_label = cand_a, "A"
        if fail_a_valid or own_run_a.failed:
            await ctx.phase("repair")
            cand_ar = await _repair(ctx, who="repairer of A", goal=goal, contract=contract, cand=cand_a, base=base,
                                    indep=indep, failing=fail_a_valid, msgs=run_a.messages, peer=[],
                                    own_fail=sorted(own_run_a.failed), contested=sorted(invalid), unisolated=unisolated)
            ledger.mark("L3-repair")
            if has_diff(cand_ar):
                run_ar = ex.run_tests(base, cand_ar.diff, indep) if indep else ex.TestOutcome()
                own_run_ar = ex.run_tests(base, cand_ar.diff, own_a) if own_a else ex.TestOutcome()
                fail_ar = [k for k in run_ar.failed if k not in invalid]
                rep["L3"] = {"indep_fail_before": len(fail_a_valid), "indep_fail_after": len(fail_ar),
                             "own_fail_after": len(own_run_ar.failed)}
                if len(fail_ar) <= len(fail_a_valid):
                    cand_a_best, a_label = cand_ar, "Ar"
                if not fail_ar and not own_run_ar.failed and (indep or own_a) and early_stop:
                    return await finish(cand_ar, 3, "Ar", "repaired")

    # ---- L4 diversify: blind Coder B, cross matrix, one repair of B, select
    await ctx.phase("diversify")
    if v7:
        spec, rep["retries"]["spec"] = await _with_retry(run_spec, lambda s: isinstance(s, dict) and s.get("requirements"))
        contract, _ = _render_contract(spec)
        ledger.mark("L4-spec")
    cand_b, rep["retries"]["coder_b"] = await _with_retry(coder("implementer B", P.STYLE_B, "coder-b"), has_diff)
    ledger.mark("L4-coder-b")
    pool: dict[str, Any] = {}
    own: dict[str, dict[str, str]] = {}
    if not a_empty:
        pool[a_label] = cand_a_best
        if a_label != "A":
            pool["A"] = cand_a
        own["A"] = own_a
    if has_diff(cand_b):
        pool["B"] = cand_b
        own["B"] = _own_tests(cand_b, base)

    def build_matrix(cands: dict[str, Any]) -> an.Matrix:
        m = an.Matrix()
        for name, cand in cands.items():
            if indep:
                m.set("indep", name, {k: v for k, v in ex.run_tests(base, cand.diff, indep).cases.items()
                                      if k not in invalid})
            for author, files in own.items():
                if files:
                    m.set(f"own:{author}", name, ex.run_tests(base, cand.diff, files).cases)
        return m

    matrix = build_matrix(pool)
    authors = [n for n in (a_label, "B") if n in pool]
    suspects = an.suspect_cases(matrix, "indep", authors)
    scores = {n: an.score(matrix, n, [x for x in ("A", "B") if x in own], suspects) for n in pool}
    rep["L4"] = {n: s.__dict__ for n, s in scores.items()}
    rep["suspects"] = sorted(suspects)
    ledger.mark("L4-matrix")

    if "B" in pool and not scores["B"].clean:
        fail = an.failing_for(matrix, "B", [x for x in ("A", "B") if x in own], suspects)
        msgs = ex.run_tests(base, cand_b.diff, indep).messages if indep else {}
        cand_br = await _repair(ctx, who="repairer of B", goal=goal, contract=contract, cand=cand_b, base=base,
                                indep=indep, failing=fail["independent"], msgs=msgs, peer=fail["peer"],
                                own_fail=fail["own"], contested=fail["contested"], unisolated=unisolated)
        ledger.mark("L4-repair-b")
        if has_diff(cand_br):
            pool["Br"] = cand_br
            matrix = build_matrix(pool)
            suspects = an.suspect_cases(matrix, "indep", authors)
            scores = {n: an.score(matrix, n, [x for x in ("A", "B") if x in own], suspects) for n in pool}
            rep["L4_after_repair"] = {n: s.__dict__ for n, s in scores.items()}

    await ctx.phase("select")
    if not pool:
        tmp.cleanup()
        return {"status": "error", "error": "no candidate produced a change", "report": rep, "ledger": ledger.rows}
    best = max(s.key for s in scores.values())
    top = [n for n in pool if scores[n].key == best]
    reason = "best-evidence"
    if len(top) > 1:
        x, y = top[0], top[1]
        dis = an.disagreements(matrix, x, y, suspects)
        if dis:
            pick = await _arbitrate(ctx, goal, x, y, dis, indep)
            reason = "arbiter" if pick else "arbiter-split-smaller-diff"
            top = [pick] if pick else sorted(top, key=lambda n: len(pool[n].diff))
        else:
            reason = "tie-same-behavior-smaller-diff"
            top = sorted(top, key=lambda n: len(pool[n].diff))
    ledger.mark("select")
    return await finish(pool[top[0]], 4, top[0], reason)
