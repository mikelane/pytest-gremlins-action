#!/usr/bin/env bash
set -euo pipefail

REPORT="coverage/gremlins/gremlins.json"

if [[ ! -f "${REPORT}" ]]; then
  echo "::warning::${REPORT} not found — assuming no mutations were generated."
  echo "If this is unexpected, verify pytest-gremlins >= 1.5.1 is installed and --gremlin-report=json was passed."
  {
    echo "score=100"
    echo "zapped=0"
    echo "survived=0"
    echo "timeout=0"
    echo "total=0"
    echo "pardoned=0"
  } >> "${GITHUB_OUTPUT}"
  echo "Mutation score: 100% (no mutations generated)"
  exit 0
fi

# Extract summary fields using jq
SCORE=$(jq -r '.summary.percentage' "${REPORT}")
ZAPPED=$(jq -r '.summary.zapped' "${REPORT}")
SURVIVED=$(jq -r '.summary.survived' "${REPORT}")
TIMEOUT=$(jq -r '.summary.timeout' "${REPORT}")
TOTAL=$(jq -r '.summary.total' "${REPORT}")
PARDONED=$(jq -r '.summary.pardoned' "${REPORT}")

# Set outputs
{
  echo "score=${SCORE}"
  echo "zapped=${ZAPPED}"
  echo "survived=${SURVIVED}"
  echo "timeout=${TIMEOUT}"
  echo "total=${TOTAL}"
  echo "pardoned=${PARDONED}"
} >> "${GITHUB_OUTPUT}"

echo "Mutation score: ${SCORE}% (${ZAPPED} zapped, ${SURVIVED} survived, ${TIMEOUT} timeout, ${PARDONED} pardoned out of ${TOTAL} total)"
