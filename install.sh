#!/usr/bin/env bash
# seo-operator installer.
#
#   ./install.sh                 skills into ~/.claude/skills (all projects)
#   ./install.sh --project       skills into ./.claude/skills (this project only)
#
# Existing skills with the same name are backed up to <name>.bak.<timestamp> first.
# The state folder (.seo/<site>/) is created later by seo_state.py init, not here.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude"
while [ $# -gt 0 ]; do
  case "$1" in
    --project) DEST="$(pwd)/.claude" ;;
    -h|--help) sed -n 2,8p "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

mkdir -p "$DEST/skills"
for s in "$HERE"/skills/*/; do
  name="$(basename "$s")"
  if [ -d "$DEST/skills/$name" ]; then
    mv "$DEST/skills/$name" "$DEST/skills/$name.bak.$(date +%s)"
    echo "backed up existing $name"
  fi
  cp -R "$s" "$DEST/skills/$name"
  echo "installed skill $name"
done
# seo_state.py init reads the note templates from here
mkdir -p "$DEST/skills/seo-operator/templates"
cp "$HERE"/templates/* "$DEST/skills/seo-operator/templates/"

command -v python3 >/dev/null || command -v py >/dev/null || \
  echo "note: the scripts need Python 3.9+ (standard library only)."
echo "done. Try: \"do SEO for acme-coffee.com\" or \"check robots.txt for AI bots\""
