#!/usr/bin/env bash
set -euo pipefail

# Build pytest command
CMD="pytest --gremlins --gremlin-report=json"

if [ "${INPUT_PARALLEL}" = "true" ]; then
  CMD="${CMD} --gremlin-parallel"
fi

if [ -n "${INPUT_WORKERS}" ]; then
  CMD="${CMD} --gremlin-workers=${INPUT_WORKERS}"
fi

if [ "${INPUT_CACHE}" = "true" ]; then
  CMD="${CMD} --gremlin-cache"
fi

if [ -n "${INPUT_TARGETS}" ]; then
  CMD="${CMD} --gremlin-targets=${INPUT_TARGETS}"
fi

if [ -n "${INPUT_EXTRA_ARGS}" ]; then
  CMD="${CMD} ${INPUT_EXTRA_ARGS}"
fi

echo "::group::Running pytest-gremlins"
echo "Command: ${CMD}"
eval "${CMD}"
echo "::endgroup::"
