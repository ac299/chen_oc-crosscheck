"""Reference solution (never shown to agents).

Segment-level DP: a `**` pattern segment consumes zero or more path segments,
every other pattern segment matches exactly one path segment through a
memoised character DP. Both levels are polynomial.
"""

from functools import lru_cache


def _split(pattern):
    """Split on '/' that is not escaped."""
    parts, cur, i = [], [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            cur.append(pattern[i:i + 2])
            i += 2
            continue
        if ch == "/":
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def _parse_class(seg, i):
    j = i + 1
    neg = False
    if j < len(seg) and seg[j] in "!^":
        neg, j = True, j + 1
    items, first = [], True
    while j < len(seg):
        ch = seg[j]
        if ch == "]" and not first:
            return ("class", neg, tuple(items)), j + 1
        first = False
        if ch == "\\" and j + 1 < len(seg):
            items.append((seg[j + 1], seg[j + 1]))
            j += 2
            continue
        if j + 2 < len(seg) and seg[j + 1] == "-" and seg[j + 2] != "]":
            items.append((seg[j], seg[j + 2]))
            j += 3
            continue
        items.append((ch, ch))
        j += 1
    return None


def _tokens(seg):
    toks, i = [], 0
    while i < len(seg):
        ch = seg[i]
        if ch == "\\":
            toks.append(("lit", seg[i + 1]))
            i += 2
        elif ch == "*":
            if not toks or toks[-1] != ("star",):
                toks.append(("star",))
            i += 1
        elif ch == "?":
            toks.append(("any",))
            i += 1
        elif ch == "[":
            parsed = _parse_class(seg, i)
            if parsed is None:
                toks.append(("lit", "["))
                i += 1
            else:
                toks.append(parsed[0])
                i = parsed[1]
        else:
            toks.append(("lit", ch))
            i += 1
    return tuple(toks)


def _one(tok, ch):
    kind = tok[0]
    if kind == "lit":
        return ch == tok[1]
    if kind == "any":
        return ch != "/"
    _, neg, items = tok
    inside = any(lo <= ch <= hi for lo, hi in items)
    return ch != "/" and (inside != neg)


def _seg_match(toks, text):
    @lru_cache(maxsize=None)
    def go(ti, ci):
        if ti == len(toks):
            return ci == len(text)
        tok = toks[ti]
        if tok[0] == "star":
            return go(ti + 1, ci) or (ci < len(text) and go(ti, ci + 1))
        return ci < len(text) and _one(tok, text[ci]) and go(ti + 1, ci + 1)

    return go(0, 0)


def match(pattern, path):
    trailing = len(pattern) - len(pattern.rstrip("\\"))
    if trailing % 2 == 1:
        raise ValueError("trailing backslash")
    psegs = []
    for seg in _split(pattern):
        if seg == "**":
            if not psegs or psegs[-1] != "**":
                psegs.append("**")
        else:
            psegs.append(_tokens(seg))
    segs = path.split("/")

    @lru_cache(maxsize=None)
    def go(pi, si):
        if pi == len(psegs):
            return si == len(segs)
        p = psegs[pi]
        if p == "**":
            return go(pi + 1, si) or (si < len(segs) and go(pi, si + 1))
        return si < len(segs) and _seg_match(p, segs[si]) and go(pi + 1, si + 1)

    if path == "" and psegs == ["**"]:
        return True
    return go(0, 0)
