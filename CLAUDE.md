# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Actions composite action that wraps [pytest-gremlins](https://github.com/mikelane/pytest-gremlins) mutation testing for CI pipelines. Installs pytest-gremlins, runs mutation testing, parses results, ratchets scores, posts PR comments, and generates badges.

## Repository Layout

- `action.yml` — composite action definition (inputs, outputs, step orchestration)
- `scripts/` — bash scripts called from action.yml steps
- `.github/workflows/ci.yml` — validates YAML and runs shellcheck on scripts
- `.github/workflows/integration-test.yml` — end-to-end test against a fixture project
- `docs/spikes/` — spike decision docs (never merged to main)
- `docs/plans/` — implementation plans

## How the Action Works

1. Restore `.gremlin-cache.db` via `actions/cache` (if `cache: 'true'`)
2. `pip install pytest-gremlins`
3. Run `pytest --gremlins --gremlin-report=json` with flags built from inputs
4. Parse `gremlin-report.json` with `jq` → set GitHub outputs
5. Ratchet: compare score against `.gremlins-score`, fail if decreased, auto-commit if improved
6. Post/update PR comment with mutation report (deduplicated via HTML marker)
7. Generate shields.io badge URL

## pytest-gremlins Key Facts

- `--gremlins` activates mutation testing (without it, pytest runs normally)
- Parallelism: `--gremlin-parallel` / `--gremlin-workers=N` — uses ProcessPoolExecutor, NOT xdist
- Cache: `--gremlin-cache` — SQLite at `.gremlin-cache.db`, keyed by content hash
- Score = (zapped + timeout) / (total - pardoned) * 100
- JSON report: `--gremlin-report=json` writes to `coverage/gremlins/gremlins.json` (requires >= 1.6.0)
- JSON report schema: `summary.{percentage, zapped, survived, timeout, total, pardoned}`
- Config in `pyproject.toml` under `[tool.pytest-gremlins]` — the action reads from there automatically

## Development

- Validate YAML: `python3 -c "import yaml; yaml.safe_load(open('action.yml'))"`
- Check scripts: `shellcheck scripts/*.sh`
- Test locally: push a branch — CI and integration-test workflows validate everything
- Commit style: Conventional Commits (`type(scope): summary`)

## Architecture

Composite action (not Docker, not JavaScript). External bash scripts in `scripts/` for testability and maintainability. PR comments via GitHub REST API with `curl`. Cache via `actions/cache@v4`. Ratchet auto-commits via `GITHUB_TOKEN`.
