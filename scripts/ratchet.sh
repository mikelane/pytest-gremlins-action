#!/usr/bin/env bash
set -euo pipefail

SCORE="${INPUT_SCORE}"
RATCHET_FILE="${INPUT_RATCHET_FILE}"

# Validate score is numeric
if [[ ! "${SCORE}" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  echo "::error::SCORE must be numeric, got '${SCORE}'"
  exit 1
fi

# Read current threshold (default 0 on first run)
if [[ -f "${RATCHET_FILE}" ]]; then
  THRESHOLD=$(tr -d '[:space:]' < "${RATCHET_FILE}")
else
  THRESHOLD="0"
fi

# Validate threshold is numeric
if [[ ! "${THRESHOLD}" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  echo "::error::THRESHOLD must be numeric, got '${THRESHOLD}'"
  exit 1
fi

echo "Current score: ${SCORE}%, threshold: ${THRESHOLD}%"

# Compare using awk for float comparison (pass variables safely via -v)
PASSED=$(awk -v score="${SCORE}" -v threshold="${THRESHOLD}" 'BEGIN { print (score >= threshold) ? "true" : "false" }')
echo "passed=${PASSED}" >> "${GITHUB_OUTPUT}"
echo "threshold=${THRESHOLD}" >> "${GITHUB_OUTPUT}"

if [[ "${PASSED}" = "false" ]]; then
  echo "::error::Mutation score ${SCORE}% is below ratchet threshold ${THRESHOLD}%"
  exit 1
fi

# Update ratchet file if score improved
IMPROVED=$(awk -v score="${SCORE}" -v threshold="${THRESHOLD}" 'BEGIN { print (score > threshold) ? "true" : "false" }')

if [[ "${IMPROVED}" = "true" ]]; then
  echo "${SCORE}" > "${RATCHET_FILE}"
  echo "Score improved from ${THRESHOLD}% to ${SCORE}% — updating ${RATCHET_FILE}"

  # Auto-commit the updated ratchet file
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git add "${RATCHET_FILE}"
  git commit -m "chore: update mutation score to ${SCORE}%"
  git push origin HEAD
  echo "Committed and pushed updated ${RATCHET_FILE}"
else
  echo "Score unchanged at ${SCORE}%"
fi
