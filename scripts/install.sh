#!/usr/bin/env bash
# Install Startup Skills into a Claude Code skills directory by symlinking.
# Symlinks keep each skill connected to the shared engine (bin/, lib/) and
# knowledge base in this repository.
#
#   scripts/install.sh                      # all skills -> ~/.claude/skills
#   scripts/install.sh pitch-deck-maker     # one skill (plus nothing else needed)
#   scripts/install.sh --project /path/repo # into <repo>/.claude/skills
#   scripts/install.sh --target DIR         # any skills directory
#   scripts/install.sh --uninstall [skill…]
set -euo pipefail
ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$HOME/.claude/skills"
MODE=install
SKILLS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --project) TARGET="$2/.claude/skills"; shift 2 ;;
    --uninstall) MODE=uninstall; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) SKILLS+=("$1"); shift ;;
  esac
done
if [ ${#SKILLS[@]} -eq 0 ]; then
  for d in "$ROOT"/skills/*/; do SKILLS+=("$(basename "$d")"); done
fi
mkdir -p "$TARGET"
for s in "${SKILLS[@]}"; do
  src="$ROOT/skills/$s"
  dst="$TARGET/$s"
  [ -f "$src/SKILL.md" ] || { echo "unknown skill: $s" >&2; exit 1; }
  if [ "$MODE" = uninstall ]; then
    if [ -L "$dst" ]; then rm "$dst"; echo "removed $dst"; else echo "skip $dst (not a symlink we created)"; fi
    continue
  fi
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then echo "skip $dst: exists and is not a symlink" >&2; continue; fi
  ln -sfn "$src" "$dst"
  echo "linked $dst -> $src"
done
if [ "$MODE" = install ]; then
  if [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo; echo "Next: create the Python environment with: $ROOT/scripts/setup.sh"
  fi
  echo "Restart Claude Code or run /reload-skills if the skills directory is new."
fi
