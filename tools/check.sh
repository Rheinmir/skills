#!/usr/bin/env bash
# check.sh — toàn bộ cổng của repo skills, chạy được cục bộ và trong CI (mục tiêu ≤ 30 s).
#   bash tools/check.sh [<checkout Rheinmir/setup>]
# Tool engine (swh-lint, skill-provenance, skill-resolve-eval, skill-requires) nằm ở repo setup — KHÔNG chép sang đây.
# Thứ tự ưu tiên tìm setup: tham số → $OVERSTACK_SETUP → ~/orca/setup → ~/.claude/harness (bản global, thiếu tool tầng 3).
set -uo pipefail
cd "$(dirname "$0")/.."
SETUP="${1:-${OVERSTACK_SETUP:-}}"
if [ -z "$SETUP" ]; then
  for c in "$HOME/orca/setup" "$HOME/.claude/harness"; do [ -f "$c/harness/scripts/skill-requires.py" ] && { SETUP="$c"; break; }; done
fi
[ -f "${SETUP:-/nonexistent}/harness/scripts/skill-requires.py" ] || { echo "✗ không thấy repo setup (truyền đường dẫn hoặc đặt OVERSTACK_SETUP)"; exit 1; }
export OVERSTACK_SETUP="$SETUP" OVERSTACK_SKILLS_DIR="$PWD/skills"
PASS=0; FAIL=0
run() { local name="$1"; shift; local t0=$(date +%s)
  if "$@" >/tmp/skills-check.$$ 2>&1; then PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m %-28s %ss\n' "$name" "$(( $(date +%s) - t0 ))"
  else FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m %-28s %ss\n' "$name" "$(( $(date +%s) - t0 ))"; sed 's/^/        /' /tmp/skills-check.$$ | tail -15; fi; }
echo "repo skills · setup = $SETUP"
run "registry (yaml·name·loop·market)" python3 tools/registry.py --check
run "requires khớp grep"            python3 "$SETUP/harness/scripts/skill-requires.py" gen --check --skills-dir skills --repo-root "$SETUP"
run "requires đủ ở setup HEAD"       python3 "$SETUP/harness/scripts/skill-requires.py" check --skills-dir skills --repo-root "$SETUP" --ci
run "swh-lint (cấu trúc native)"     python3 "$SETUP/fdk/tools/swh-lint.py" --root "$PWD" --ci
run "provenance checksum"           python3 "$SETUP/fdk/tools/skill-provenance.py" --skills-dir skills --store skills.provenance.json check --ci
run "skill-resolve golden"          python3 "$SETUP/harness/scripts/skill-resolve-eval.py" --check --skills-dir skills --goldens evals/skill-resolve
run "catalog + version stamp"       python3 tools/catalog.py --check
rm -f /tmp/skills-check.$$
echo "→ $PASS PASS · $FAIL FAIL"
[ "$FAIL" = 0 ]
