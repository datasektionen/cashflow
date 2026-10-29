#!/usr/bin/env bash
# Adds shadcn components. The CLI cannot resolve the `#/` alias for utils and
# writes `from "cn"`, so fix the import and drop the bogus package afterwards.
set -euo pipefail
cd "$(dirname "$0")/.."
bunx --bun shadcn@latest add -y "$@"
sed -i 's|from "cn"|from "#/lib/utils"|' src/components/ui/*.tsx
bun remove cn next-themes >/dev/null 2>&1 || true
