#!/usr/bin/env bash
# RDA installer -- one canonical pack, every environment.
#
# Strategy: install the canonical Agent Skills tree at .agents/skills/ (project) or ~/.agents/skills/ (user),
# which Codex, Cursor, Gemini CLI, GitHub Copilot/VS Code and Devin Desktop all discover natively, then symlink
# .claude/skills/ for Claude Code (which reads only its own path but follows symlinks and de-duplicates
# targets reachable from more than one location). Rule-style files are generated per tool.
#
# Usage: install.sh [--target DIR] [--scope project|user] [--profile P1..P7|P4A|P4B] [--tools claude,cursor,codex,...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$(pwd)"; SCOPE="project"; PROFILE="P3"; TOOLS="all"

while [ $# -gt 0 ]; do
  case "$1" in
    --target)  TARGET="$2"; shift 2 ;;
    --scope)   SCOPE="$2";  shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --tools)   TOOLS="$2";  shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
want() { [ "$TOOLS" = "all" ] || printf '%s' ",$TOOLS," | grep -q ",$1,"; }

case "$PROFILE" in
  P1) IDS="00 01 02 03 07 08 09 10 11 13 18 26 28 32 33 34 36" ;;
  P2) IDS="00 01 02 03 04 05 06 07 08 09 10 11 13 18 19 20 21 22 26 28 29 32 33 34 36" ;;
  P3) IDS="ALL" ;;
  P4) IDS="00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 26 28 29 30 31 32 33 34 35 36 37" ;;
  P4A) IDS="00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 19" ;;
  P4B) IDS="00 01 02 18 19 20 21 22 23 24 26 28 29 30 31 32 33 34 35 36 37" ;;
  P5) IDS="00 01 02 03 06 08 09 10 11 12 13 14 19 20 32 33 34 36" ;;
  P6) IDS="00 01 02 03 06 07 08 09 18 19 20 21 22 23 32 33 34 36" ;;
  P7) IDS="00 01 02 03 04 06 07 08 09 26 28 29 32 33 34 36" ;;
  # An unrecognised profile previously fell through to a silent full install, so a typo produced a
  # different audit than the one requested. Fail instead.
  *)  echo "unknown profile: $PROFILE (expected P1 P2 P3 P4 P4A P4B P5 P6 P7)" >&2; exit 2 ;;
esac

# Prefer python3, fall back to python (Windows/Git Bash and some minimal images ship only `python`).
# Probe by executing, not by command -v: Windows ships a `python3` App Execution Alias that resolves on
# PATH but exits non-zero with a Microsoft Store advert, which would silently break the install.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -z "$PY" ] && { echo "a working python3 (or python) is required" >&2; exit 3; }

if [ "$SCOPE" = "user" ]; then CANON="$HOME/.agents/skills"; CLAUDE="$HOME/.claude/skills"
else CANON="$TARGET/.agents/skills"; CLAUDE="$TARGET/.claude/skills"; fi
mkdir -p "$CANON" "$CLAUDE"

echo "Installing RDA profile $PROFILE ($SCOPE scope) into $CANON"
n=0
for d in "$HERE"/skills/*/; do
  slug="$(basename "$d")"
  if [ "$IDS" != "ALL" ]; then
    num="$(printf '%s' "$slug" | sed -n 's/^rda-\([0-9][0-9]\).*/\1/p')"
    printf '%s' " $IDS " | grep -q " $num " || continue
  fi
  rm -rf "${CANON:?}/$slug"; cp -R "$d" "$CANON/$slug"
  # Claude Code: symlink rather than copy, so one target serves both discovery paths.
  rm -rf "${CLAUDE:?}/$slug"
  ln -s "$CANON/$slug" "$CLAUDE/$slug" 2>/dev/null || cp -R "$d" "$CLAUDE/$slug"
  n=$((n+1))
done
echo "  installed $n skills"

# Shared resources the skills reference. Follow --scope: a user-scope install must not seed a
# project directory that the user did not ask to modify.
if [ "$SCOPE" = "user" ]; then RES="$HOME/.agents/rda"; else RES="$TARGET/.agents/rda"; fi
for sub in schemas scripts governance templates workflows; do
  mkdir -p "$RES/$sub"; cp -R "$HERE/$sub/." "$RES/$sub/" 2>/dev/null || true
done
echo "  shared resources -> $RES"

# Generate adapters into a temporary directory. Writing them back into $HERE/adapters/generated made
# installing mutate the framework itself and fail outright on a read-only or shared installation.
G="$(mktemp -d 2>/dev/null || echo "${TMPDIR:-/tmp}/rda-adapters.$$")"; mkdir -p "$G"
trap 'rm -rf "$G"' EXIT
"$PY" "$HERE/scripts/generate_adapters.py" --skills "$HERE/skills" \
      --out "$G" --profile "$PROFILE" >/dev/null

place() { mkdir -p "$(dirname "$2")"; cp "$1" "$2"; echo "  + ${2#$TARGET/}"; }
want claude   && place "$G/AGENTS.md" "$TARGET/CLAUDE.md" || true
want cursor   && place "$G/cursor/.cursor/rules/rda-core.mdc" "$TARGET/.cursor/rules/rda-core.mdc" || true
want copilot  && place "$G/copilot/.github/copilot-instructions.md" "$TARGET/.github/copilot-instructions.md" || true
want copilot  && place "$G/copilot/.github/instructions/rda-core.instructions.md" "$TARGET/.github/instructions/rda-core.instructions.md" || true
want copilot  && { mkdir -p "$TARGET/.github/skills"; cp -R "$CANON/." "$TARGET/.github/skills/" ; echo "  + .github/skills (head-branch read during PR review)"; } || true
want devin    && place "$G/devin/.devin/rules/rda-core.md" "$TARGET/.devin/rules/rda-core.md" || true
want windsurf && place "$G/windsurf/.windsurf/rules/rda-core.md" "$TARGET/.windsurf/rules/rda-core.md" || true
want antigravity && place "$G/antigravity/.agents/rules/rda-core.md" "$TARGET/.agents/rules/rda-core.md" || true
want aider    && { place "$G/aider/CONVENTIONS.md" "$TARGET/CONVENTIONS.md"; place "$G/aider/.aider.conf.yml" "$TARGET/.aider.conf.yml"; } || true
want roocode  && { place "$G/roocode/.roomodes" "$TARGET/.roomodes"; mkdir -p "$TARGET/.roo/rules-rda-audit"; cp "$G/roocode/.roo/rules-rda-audit/00-contract.md" "$TARGET/.roo/rules-rda-audit/"; } || true
want gemini   && { mkdir -p "$TARGET/.gemini/commands/rda"; cp "$G"/gemini/.gemini/commands/rda/*.toml "$TARGET/.gemini/commands/rda/"; echo "  + .gemini/commands/rda/*.toml"; } || true
want codex    && place "$G/AGENTS.md" "$TARGET/AGENTS.md" || true

echo
"$PY" "$HERE/scripts/validate_pack.py" "$CANON" || true
cat <<'NOTE'

Notes
  * Codex truncates the startup skill list at ~2% of context (8,000 chars fallback). If the metadata budget
    above is over, install a profile rather than the full pack.
  * Gemini CLI gates skill activation behind a consent prompt; expect one approval per skill on first use.
  * GitHub Copilot reads instructions and skills from the HEAD BRANCH during PR review -- merge before relying
    on them there. Invalid characters or namespace prefixes in a skill name fail silently.
  * Devin Desktop prefers .devin/ with .windsurf/ as fallback; both are written when selected.
  * Copilot Workspace was retired in May 2025; target Copilot cloud agent / code review / VS Code agent mode.
NOTE
