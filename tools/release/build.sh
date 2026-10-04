#!/bin/bash
# Cross-compiles the four release binaries and writes their checksums. Never uploads.
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
cd "$ROOT"
VERSION=$(tr -d ' \n\r' < bin/VERSION)
OUT_DIR=${OUT_DIR:-tools/release/dist}
SUMS_FILE=${SUMS_FILE:-bin/SHA256SUMS}
if command -v go >/dev/null 2>&1; then
  GO=$(command -v go)
else
  GO=""
  for c in "$HOME/.local/go/bin/go" /usr/local/go/bin/go /opt/homebrew/bin/go; do
    if [ -x "$c" ]; then GO="$c"; break; fi
  done
  [ -n "$GO" ] || { echo "build.sh: no Go toolchain" >&2; exit 1; }
fi
COMMIT=$(git rev-parse --short=12 HEAD 2>/dev/null) || COMMIT=unknown
mkdir -p "$OUT_DIR"
OUT_ABS=$(cd "$OUT_DIR" && pwd -P)
for os in linux darwin; do
  for arch in amd64 arm64; do
    (cd tools/workflow && CGO_ENABLED=0 GOOS=$os GOARCH=$arch GOTOOLCHAIN=local "$GO" build -trimpath \
      -ldflags "-X main.version=$VERSION -X main.commit=$COMMIT" \
      -o "$OUT_ABS/workflow-$os-$arch" ./cmd/workflow)
  done
done
tmp="$SUMS_FILE.tmp.$$"
(cd "$OUT_ABS" && for f in workflow-*; do
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$f"; else shasum -a 256 "$f"; fi
done) | sort -k2 > "$tmp"
mv "$tmp" "$SUMS_FILE"
