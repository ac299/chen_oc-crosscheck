"""Offline reproduction: a session that is resumed after DONE and then stops on
its token allowance leaves no record of that stop in the event stream.

No model API is used; the session is driven by the framework's own test fakes.

Scenario (what a team lead or teammate does when a message wakes it again):
  1. turn 1: the model answers -> session DONE ("completed"); session_terminal #1
  2. a new user turn is queued (as message delivery does for a team member)
  3. turn 2: the model call costs more than the remaining allowance
     -> session STOPPED ("budget ...")
Expected: the event stream's terminal record matches the final state.

Run inside the experiment container with the framework checkout to test mounted
at /kaohe/vendor/OpenCollab and as the working directory:
  /venv/bin/python /kaohe/oc-crosscheck/scripts/repro_terminal_trace.py
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, ".")

from opencollab.domain.session import SessionState  # noqa: E402
from tests.support.session_run_loop_test_support import (  # noqa: E402
    FakeLLM,
    build_runner,
    llm_response,
    run,
)


class FakeTracer:
    def __init__(self):
        self.steps = []

    def log_step(self, **event):
        self.steps.append(event)

    def flush(self):
        pass


def main() -> None:
    tracer = FakeTracer()
    state = SessionState(messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": "task"}])
    runner = build_runner(
        state=state,
        llm=FakeLLM([
            llm_response(content="first answer", total_tokens=5),
            llm_response(content="second answer", total_tokens=500),
        ]),
        tracer=tracer,
        max_budget_tokens=200,
    )
    run(runner.run_loop())
    after_turn_1 = (state.phase.value, state.terminal_reason)
    state.append_queued_external_user_turn("message from a teammate: please re-check")
    run(runner.run_loop())
    terminal = [s["payload"] for s in tracer.steps if s["step_type"] == "session_terminal"]
    out = {
        "after_turn_1": after_turn_1,
        "final_state": (state.phase.value, state.terminal_reason, state.used_tokens),
        "session_terminal_records": [(p["phase"], p["terminal_reason"], p["used_tokens"]) for p in terminal],
        "last_record_matches_final_state": bool(terminal) and terminal[-1]["phase"] == state.phase.value
        and terminal[-1]["terminal_reason"] == state.terminal_reason,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
