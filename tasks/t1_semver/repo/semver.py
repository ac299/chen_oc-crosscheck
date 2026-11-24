"""Semantic Versioning 2.0.0 parsing and comparison."""

import re

_VERSION = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)


def parse(version):
    """Return (major, minor, patch, prerelease, build)."""
    match = _VERSION.match(version)
    if not match:
        raise ValueError(f"invalid version: {version!r}")
    major, minor, patch, pre, build = match.groups()
    prerelease = tuple(pre.split(".")) if pre else ()
    metadata = tuple(build.split(".")) if build else ()
    return int(major), int(minor), int(patch), prerelease, metadata


def compare(a, b):
    """Return -1, 0 or 1 when a is lower than, equal to or higher than b."""
    va, vb = parse(a), parse(b)
    if va[:3] != vb[:3]:
        return -1 if va[:3] < vb[:3] else 1
    if va[3] != vb[3]:
        if not va[3]:
            return 1
        if not vb[3]:
            return -1
        return -1 if va[3] < vb[3] else 1
    if va[4] != vb[4]:
        return -1 if va[4] < vb[4] else 1
    return 0
