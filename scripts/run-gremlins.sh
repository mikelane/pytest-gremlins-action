#!/usr/bin/env bash
set -euo pipefail

# Build pytest command as an array for safe execution
CMD=(pytest --gremlins --gremlin-report=json)

if [[ "${INPUT_PARALLEL}" = "true" ]]; then
  CMD+=(--gremlin-parallel)
fi

if [[ -n "${INPUT_WORKERS}" ]]; then
  if [[ ! "${INPUT_WORKERS}" =~ ^[0-9]+$ ]] || [[ "${INPUT_WORKERS}" -eq 0 ]]; then
    echo "::error::INPUT_WORKERS must be a positive integer, got '${INPUT_WORKERS}'"
    exit 1
  fi
  CMD+=("--gremlin-workers=${INPUT_WORKERS}")
fi

if [[ "${INPUT_CACHE}" = "true" ]]; then
  CMD+=(--gremlin-cache)
fi

if [[ -n "${INPUT_TARGETS}" ]]; then
  CMD+=("--gremlin-targets=${INPUT_TARGETS}")
fi

if [[ -n "${INPUT_EXTRA_ARGS}" ]]; then
  read -ra EXTRA <<< "${INPUT_EXTRA_ARGS}"
  CMD+=("${EXTRA[@]}")
fi

echo "::group::Running pytest-gremlins"
echo "Command: ${CMD[*]}"
"${CMD[@]}"
echo "::endgroup::"
