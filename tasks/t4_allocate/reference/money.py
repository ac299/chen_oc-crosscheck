"""Reference solution (never shown to agents)."""


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def allocate(total, weights):
    if not _is_int(total):
        raise ValueError("total must be an int")
    if not isinstance(weights, list) or not weights:
        raise ValueError("weights must be a non-empty list")
    if not all(_is_int(w) and w >= 0 for w in weights):
        raise ValueError("weights must be non-negative ints")
    wsum = sum(weights)
    if wsum <= 0:
        raise ValueError("weights must have a positive sum")
    amount = abs(total)
    floors = [amount * w // wsum for w in weights]
    rems = [amount * w % wsum for w in weights]
    left = amount - sum(floors)
    order = sorted(range(len(weights)), key=lambda i: (-rems[i], i))
    for i in order[:left]:
        floors[i] += 1
    return [-x for x in floors] if total < 0 else floors
