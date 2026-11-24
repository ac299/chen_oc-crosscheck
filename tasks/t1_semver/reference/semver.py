"""Reference solution (never shown to agents)."""

import re

_NUM = r"0|[1-9][0-9]*"
_ID = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})(?:-({_ID}(?:\.{_ID})*))?(?:\+({_ID}(?:\.{_ID})*))?"
)


def parse(version):
    match = _VERSION.fullmatch(version)
    if not match:
        raise ValueError(f"invalid version: {version!r}")
    major, minor, patch, pre, build = match.groups()
    prerelease = tuple(pre.split(".")) if pre else ()
    for ident in prerelease:
        if ident.isdigit() and len(ident) > 1 and ident[0] == "0":
            raise ValueError(f"leading zero in prerelease: {version!r}")
    metadata = tuple(build.split(".")) if build else ()
    return int(major), int(minor), int(patch), prerelease, metadata


def compare(a, b):
    va, vb = parse(a), parse(b)
    if va[:3] != vb[:3]:
        return -1 if va[:3] < vb[:3] else 1
    pa, pb = va[3], vb[3]
    if pa == pb:
        return 0
    if not pa:
        return 1
    if not pb:
        return -1
    for x, y in zip(pa, pb):
        if x == y:
            continue
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn:
            return -1 if int(x) < int(y) else 1
        if xn:
            return -1
        if yn:
            return 1
        return -1 if x < y else 1
    return -1 if len(pa) < len(pb) else 1
