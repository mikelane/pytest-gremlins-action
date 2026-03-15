#!/usr/bin/env bash
set -euo pipefail

SCORE="${INPUT_SCORE}"
RATCHET_FILE="${INPUT_RATCHET_FILE}"

# Read current threshold (default 0 on first run)
if [ -f "${RATCHET_FILE}" ]; then
  THRESHOLD=$(tr -d '[:space:]' < "${RATCHET_FILE}")
else
  THRESHOLD="0"
fi

echo "Current score: ${SCORE}%, threshold: ${THRESHOLD}%"

# Compare using awk for float comparison
PASSED=$(awk "BEGIN { print (${SCORE} >= ${THRESHOLD}) ? \"true\" : \"false\" }")
echo "passed=${PASSED}" >> "${GITHUB_OUTPUT}"

if [ "${PASSED}" = "false" ]; then
  echo "::error::Mutation score ${SCORE}% is below ratchet threshold ${THRESHOLD}%"
  exit 1
fi

# Update ratchet file if score improved
IMPROVED=$(awk "BEGIN { print (${SCORE} > ${THRESHOLD}) ? \"true\" : \"false\" }")

if [ "${IMPROVED}" = "true" ]; then
  echo "${SCORE}" > "${RATCHET_FILE}"
  echo "Score improved from ${THRESHOLD}% to ${SCORE}% — updating ${RATCHET_FILE}"

  # Auto-commit the updated ratchet file
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git add "${RATCHET_FILE}"
  git commit -m "chore: update mutation score to ${SCORE}%"
  git push
  echo "Committed and pushed updated ${RATCHET_FILE}"
else
  echo "Score unchanged at ${SCORE}%"
fi
