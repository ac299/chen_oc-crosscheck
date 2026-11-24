#!/usr/bin/env bash
# Resumable parallel download by HTTP range, with per-chunk retries and sha256 check.
#   scripts/fetch_parallel.sh <url> <out_file> <size_bytes> <sha256> [jobs] [chunk_mb]
set -uo pipefail
URL="$1"; OUT="$2"; SIZE="$3"; SHA="$4"; JOBS="${5:-8}"; CHUNK=$(( ${6:-50} * 1024 * 1024 ))
PROXY="${PROXY:-http://127.0.0.1:7877}"
PARTS="$OUT.parts"; mkdir -p "$PARTS"
N=$(( (SIZE + CHUNK - 1) / CHUNK ))

fetch() {
  i="$1"; start=$(( i * CHUNK )); end=$(( start + CHUNK - 1 )); [ "$end" -ge "$SIZE" ] && end=$(( SIZE - 1 ))
  want=$(( end - start + 1 )); f="$PARTS/$(printf %05d "$i")"
  for attempt in 1 2 3 4 5 6 7 8; do
    have=$(stat -c %s "$f" 2>/dev/null || echo 0)
    [ "$have" -eq "$want" ] && return 0
    [ "$have" -gt "$want" ] && { rm -f "$f"; have=0; }
    curl -sS -m 600 -x "$PROXY" -L -r "$(( start + have ))-$end" "$URL" >> "$f" 2>/dev/null
  done
  have=$(stat -c %s "$f" 2>/dev/null || echo 0)
  [ "$have" -eq "$want" ] || { echo "chunk $i failed ($have/$want)"; return 1; }
}
export -f fetch; export URL SIZE CHUNK PARTS PROXY
seq 0 $(( N - 1 )) | xargs -P "$JOBS" -I{} bash -c 'fetch {}'
cat "$PARTS"/* > "$OUT.tmp"
got=$(stat -c %s "$OUT.tmp"); sum=$(sha256sum "$OUT.tmp" | cut -d" " -f1)
if [ "$got" = "$SIZE" ] && [ "$sum" = "$SHA" ]; then mv "$OUT.tmp" "$OUT"; rm -rf "$PARTS"; echo "OK $OUT $got bytes sha256 verified"
else echo "MISMATCH size=$got sha=$sum (parts kept in $PARTS for resume)"; rm -f "$OUT.tmp"; exit 1; fi
