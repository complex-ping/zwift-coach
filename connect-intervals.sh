#!/bin/sh
# Registers the Intervals.icu MCP server with Claude Code. The key is not echoed or saved in shell history.
set -eu
printf 'Intervals API key (hidden): '
stty -echo
trap 'stty echo' EXIT
read -r key
stty echo
echo
printf 'Athlete ID (like i123456): '
read -r athlete
if [ -z "$key" ] || [ -z "$athlete" ]; then
  echo "Both values are required. Nothing was changed."
  exit 1
fi
claude mcp add intervals-icu --scope user \
  --env INTERVALS_ICU_API_KEY="$key" \
  --env INTERVALS_ICU_ATHLETE_ID="$athlete" \
  -- uvx intervals-icu-mcp@5.8.0
echo "Done. Go back to Claude and say connected."
