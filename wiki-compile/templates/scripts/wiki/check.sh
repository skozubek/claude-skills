#!/bin/sh
set -eu

if [ -f "package.json" ] && grep -q '"lint:wiki"' package.json 2>/dev/null && command -v npm >/dev/null 2>&1; then
  npm run lint:wiki
elif command -v node >/dev/null 2>&1; then
  node scripts/wiki/validate.mjs
else
  echo "wiki check requires npm or node" >&2
  exit 1
fi
