"""Proportional allocation of integer cents."""


def allocate(total, weights):
    """Split ``total`` cents according to ``weights``."""
    weight_sum = sum(weights)
    shares = [round(total * w / weight_sum) for w in weights]
    return shares
