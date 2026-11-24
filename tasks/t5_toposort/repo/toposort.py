"""Deterministic dependency ordering."""


class CycleError(ValueError):
    pass


def build_order(deps):
    raise NotImplementedError
