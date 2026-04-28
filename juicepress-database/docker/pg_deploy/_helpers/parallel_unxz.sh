#!/bin/sh

set -euxo pipefail

anchor="${1:-/tmp/pg_deploy/tables}"

find "$anchor" -type f -name "*.xz" -print0 | \
xargs -0 -n1 -P"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)" sh -c '
  file="$1"
  out=`echo "$file" | sed "s/\.xz$//"`
  if xzcat "$file" > "$out"; then
    rm "$file"
  else
    echo "Failed to decompress: $file" >&2
  fi
' sh
