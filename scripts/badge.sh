#!/usr/bin/env bash
set -euo pipefail

SCORE="${INPUT_SCORE}"

# Validate score is numeric
if [[ ! "${SCORE}" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  echo "::error::SCORE must be numeric, got '${SCORE}'"
  exit 1
fi

# Determine color based on score (pass variable safely via -v)
COLOR=$(awk -v score="${SCORE}" 'BEGIN {
  if (score >= 80) print "brightgreen"
  else if (score >= 60) print "yellow"
  else print "red"
}')

# URL-encode the percent sign
URL="https://img.shields.io/badge/mutation_score-${SCORE}%25-${COLOR}"

echo "url=${URL}" >> "${GITHUB_OUTPUT}"
echo "Badge URL: ${URL}"
