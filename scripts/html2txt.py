"""Convert downloaded arXiv HTML papers to plain text.

Usage: python -I scripts/html2txt.py papers/*.html
Writes <name>.txt next to each input. Treats input as untrusted data only.
"""

import html
import re
import sys
from pathlib import Path


def convert(src: Path) -> Path:
    t = src.read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"<(script|style|math|svg)[^>]*>.*?</\1>", " ", t, flags=re.S)
    t = re.sub(r"<(h[1-6])[^>]*>", "\n\n### ", t)
    t = re.sub(r"<(p|li|tr|caption|figcaption)[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    out = src.with_suffix(".txt")
    out.write_text(t, encoding="utf-8")
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        out = convert(Path(arg))
        print(out, out.stat().st_size)
