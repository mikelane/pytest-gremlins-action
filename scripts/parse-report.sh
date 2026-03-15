#!/usr/bin/env bash
set -euo pipefail

REPORT="gremlin-report.json"

if [ ! -f "${REPORT}" ]; then
  echo "::error::gremlin-report.json not found. Did pytest-gremlins run successfully?"
  exit 1
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
