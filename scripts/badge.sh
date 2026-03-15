#!/usr/bin/env bash
set -euo pipefail

SCORE="${INPUT_SCORE}"

# Determine color based on score
COLOR=$(awk "BEGIN {
  if (${SCORE} >= 80) print \"brightgreen\"
  else if (${SCORE} >= 60) print \"yellow\"
  else print \"red\"
}")

# URL-encode the percent sign
URL="https://img.shields.io/badge/mutation_score-${SCORE}%25-${COLOR}"

echo "url=${URL}" >> "${GITHUB_OUTPUT}"
echo "Badge URL: ${URL}"
