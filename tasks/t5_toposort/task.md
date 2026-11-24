Implement `build_order(deps)` and the exception class `CycleError` in `toposort.py`.

- `deps` maps each node name (a string) to an iterable of prerequisite node names that must come before it. A node that appears only as a prerequisite is still part of the graph. Duplicate prerequisites are allowed and count once.
- `build_order` returns a list containing every node exactly once, with every prerequisite before the nodes that depend on it.
- When several nodes are ready at the same time, always take the one that is smallest in normal string order. So the result is the lexicographically smallest valid order, and it is fully deterministic.
- If the graph has a cycle, raise `CycleError`. It must be a subclass of `ValueError` and have the attribute `nodes`: the sorted list of every node that lies on at least one cycle, including a node that lists itself as its own prerequisite. Nodes that only depend on a cycle, or that a cycle depends on, are not on a cycle and must not be listed.
- `deps` must not be modified.

Run the tests with `python -m pytest -q`.
