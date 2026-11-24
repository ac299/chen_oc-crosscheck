"""Sample 10 IO2CodeBench tasks and write them in the tasks/ format (docs/io2code-protocol.md).

Run inside a container WITHOUT network, with the IO2Code checkout mounted read-only
at /io2code and the project mounted at /kaohe/oc-crosscheck:
  python repobench/make_io2code_tasks.py
It imports IO2Code's own adapter (benchmark code) only inside that container.

Output: tasks_io/io_<task>/{task.md, repo/program.py, repo/tests/test_basic.py,
hidden/test_hidden.py, reference/program.py, meta.json}
"""

from __future__ import annotations

import ast
import inspect
import json
import random
import sys
import textwrap
from pathlib import Path

import os

# Development sample (docs/io2code-protocol.md): seed 20261121, 10 tasks, tasks_io/.
# Held-out test sample (docs/heldout-test-protocol.md): XC_IO_SEED=20261122,
# XC_IO_N=20, XC_IO_OUT=tasks_io_test, excluding the development tasks.
SEED = int(os.environ.get("XC_IO_SEED", "20261121"))
N = int(os.environ.get("XC_IO_N", "10"))
ROOT = Path("/kaohe/oc-crosscheck")
IO = Path("/io2code/DIO-Agent-experiments")
OUT = ROOT / os.environ.get("XC_IO_OUT", "tasks_io")
EXCLUDE_DIR = os.environ.get("XC_IO_EXCLUDE", "")  # folder whose meta.json task names are excluded

sys.path.insert(0, "/kaohe/vendor/OpenCollab/examples/io2code_oc")
import tasks as io_tasks  # noqa: E402  (OpenCollab's example loader)

io_tasks.set_io2code_root("/io2code")

COMPARE = '''
def _match(actual, expected):
    if isinstance(expected, list) and isinstance(actual, (list, tuple)):
        return len(expected) == len(actual) and all(_match(a, e) for a, e in zip(actual, expected))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return set(expected) == set(actual) and all(_match(actual[k], expected[k]) for k in expected)
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return actual == expected if isinstance(expected, int) else abs(actual - expected) < 1e-6
    return actual == expected
'''


def jsonable(v):
    return json.loads(json.dumps(v))


def data_literal(rows) -> str:
    """Test data as a Python expression, written as json.loads(...): JSON
    true/false/null are not Python literals. Found on the held-out sample, where
    io_extra_allpositive and two geometry tasks return booleans. The development
    tasks in tasks_io/ have no booleans and were built with plain json.dumps."""
    return "json.loads(" + repr(json.dumps(rows)) + ")"


def oracle_source(task) -> str:
    fn = task.oracle
    src = textwrap.dedent(inspect.getsource(fn))
    mod = inspect.getmodule(fn)
    module_src = inspect.getsource(mod) if mod is not None else ""
    return f"# reference: the IO2Code oracle, copied from {getattr(mod, '__name__', '?')}\n{module_src}\n\n" \
           f"def {task.function_name}(input_data):\n    return {fn.__name__}(input_data)\n" if module_src else src


def main() -> None:
    names = [n for n in io_tasks.list_tasks() if not n.startswith("multimodal")]
    assert len(names) == 115, len(names)
    if EXCLUDE_DIR:
        used = {json.loads(m.read_text(encoding="utf-8"))["task"] for m in (ROOT / EXCLUDE_DIR).glob("*/meta.json")}
        assert len(used) == 10, used
        names = [n for n in names if n not in used]
        assert len(names) == 105, len(names)
    picked = random.Random(SEED).sample(sorted(names), N)
    OUT.mkdir(exist_ok=True)
    for name in picked:
        t = io_tasks.load_task(name)
        d = OUT / f"io_{name.lower()}"
        (d / "repo" / "tests").mkdir(parents=True, exist_ok=True)
        (d / "hidden").mkdir(exist_ok=True)
        (d / "reference").mkdir(exist_ok=True)
        fname = t.function_name
        (d / "repo" / "program.py").write_text(
            f'"""Reconstruct the hidden function from its examples (see task.md)."""\n\n\n'
            f"def {fname}(input_data):\n    raise NotImplementedError\n", encoding="utf-8")
        visible = [(jsonable(i), jsonable(o)) for i, o in t.visible]
        held = [(jsonable(i), jsonable(o)) for i, o in t.held_out]
        (d / "repo" / "tests" / "test_basic.py").write_text(
            "import json\n\nimport pytest\n\nfrom program import " + fname + "\n" + COMPARE +
            "\nVISIBLE = " + data_literal(visible) + "\n\n\n"
            "@pytest.mark.parametrize('inp,out', VISIBLE)\n"
            f"def test_visible(inp, out):\n    assert _match({fname}(inp), out)\n", encoding="utf-8")
        (d / "hidden" / "test_hidden.py").write_text(
            "import json\n\nimport pytest\n\nfrom program import " + fname + "\n" + COMPARE +
            "\nHELD_OUT = " + data_literal(held) + "\n\n\n"
            "@pytest.mark.parametrize('inp,out', HELD_OUT)\n"
            f"def test_held_out(inp, out):\n    assert _match({fname}(inp), out)\n", encoding="utf-8")
        (d / "reference" / "program.py").write_text(oracle_source(t), encoding="utf-8")
        examples = "\n".join(f"- `{fname}({json.dumps(i)})` returns `{json.dumps(o)}`" for i, o in visible)
        (d / "task.md").write_text(
            f"`program.py` must define `{fname}(input_data)`, a function whose behaviour is only known from the "
            f"examples below. Infer the rule and implement it so that it generalises to new inputs of the same "
            f"kind, not just these examples.\n\nInput: {t.input_type}. {t.input_constraints}\n\n"
            f"Examples:\n{examples}\n\nThe examples are also in `tests/test_basic.py`. "
            f"Run the tests with `python -m pytest -q`.\n", encoding="utf-8")
        (d / "meta.json").write_text(json.dumps({
            "task": name, "function": fname, "input_type": t.input_type, "kind": t.kind,
            "visible": len(visible), "held_out": len(held), "seed": SEED}, indent=1), encoding="utf-8")
        print("created", d.name, fname, len(visible), "visible", len(held), "held-out")


if __name__ == "__main__":
    main()
