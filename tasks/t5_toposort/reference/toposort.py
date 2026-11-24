"""Reference solution (never shown to agents)."""

import heapq


class CycleError(ValueError):
    def __init__(self, nodes):
        super().__init__(f"cycle among {nodes}")
        self.nodes = nodes


def _cycle_nodes(graph):
    # Tarjan SCC; graph: node -> set(prereqs)
    index, low, stack, on, out = {}, {}, [], set(), set()
    counter = [0]

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph[v]:
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in graph[v]:
                out.update(comp)

    for v in sorted(graph):
        if v not in index:
            strong(v)
    return sorted(out)


def build_order(deps):
    graph = {}
    for node, pres in deps.items():
        graph.setdefault(node, set()).update(pres)
        for p in pres:
            graph.setdefault(p, set())
    indeg = {n: len(p) for n, p in graph.items()}
    users = {n: [] for n in graph}
    for n, pres in graph.items():
        for p in pres:
            users[p].append(n)
    ready = [n for n, d in indeg.items() if d == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        n = heapq.heappop(ready)
        order.append(n)
        for u in users[n]:
            indeg[u] -= 1
            if indeg[u] == 0:
                heapq.heappush(ready, u)
    if len(order) != len(graph):
        raise CycleError(_cycle_nodes(graph))
    return order
