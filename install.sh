#!/bin/sh
# Copies the skill and agent into ~/.claude so they work in every project.
set -eu
root="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
rm -rf "$HOME/.claude/skills/zwift-coach"
cp -R "$root/skills/zwift-coach" "$HOME/.claude/skills/zwift-coach"
cp "$root/agents/zwift-coach.md" "$HOME/.claude/agents/zwift-coach.md"
echo "Installed the zwift-coach skill and agent."
