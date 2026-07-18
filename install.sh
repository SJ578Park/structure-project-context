#!/bin/sh
set -eu

REPO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE_DIR="$REPO_DIR/skill/structure-project-context"
CODEX_ROOT=${CODEX_HOME:-"$HOME/.codex"}
SKILLS_DIR="$CODEX_ROOT/skills"
TARGET_DIR="$SKILLS_DIR/structure-project-context"

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "Skill source not found: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"

if [ -e "$TARGET_DIR" ]; then
  BACKUP_DIR="$TARGET_DIR.backup-$(date +%Y%m%d%H%M%S)"
  mv "$TARGET_DIR" "$BACKUP_DIR"
  echo "Previous installation moved to $BACKUP_DIR"
fi

TEMP_DIR=$(mktemp -d "$SKILLS_DIR/.structure-project-context.XXXXXX")
trap 'rm -rf "$TEMP_DIR"' EXIT HUP INT TERM
cp -R "$SOURCE_DIR"/. "$TEMP_DIR"/
mv "$TEMP_DIR" "$TARGET_DIR"
trap - EXIT HUP INT TERM

echo "Installed structure-project-context at $TARGET_DIR"
echo "Restart Codex to refresh the global skill list."
