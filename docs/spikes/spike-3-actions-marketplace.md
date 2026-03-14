# Spike: Actions Marketplace Validation

**Issue:** mikelane/pytest-gremlins-action#3
**Branch:** spike/actions-marketplace (never merged)
**Time-box:** 2 working days
**Status:** Complete

## Context

Validates the composite action structure, Marketplace requirements, and key open questions
for `uses: mikelane/pytest-gremlins-action@v1` before BDD Bootstrap begins.

## Canonical Fixture

Location: `spike-fixture/` in this branch.

| Attribute | Value |
|-----------|-------|
| Source files | `mathlib.py` — 3 functions (add, multiply, is_positive) |
| Test file | `tests/test_mathlib.py` — 5 tests |
| Total gremlins | **9** |
| Parallelism observable | Yes — `Starting parallel execution with 2 workers` confirmed with `--gremlin-workers=2` |

## Findings

### Q1: Composite action step-level `if:` conditions
**Decision:** Yes — composite action steps support `if:` identically to job steps.
`if: always()` on the cache-save step is valid per the GitHub Actions runner spec.
This is the critical pattern: cache must save even when threshold check fails (non-zero exit).

### Q2: xdist compatibility — re-validated on Python 3.12 with v1.5.0b8

**Updated decision:** The original spike ran on Python 3.14, which has a separate
incompatibility with `OperatorRegistry`. That bug masked the real xdist behavior.
On Python 3.12 + v1.5.0b8, `pytest --gremlins -n 2` works correctly:

```
Zapped: 9 gremlins (100%)
Survived: 0 gremlins (0%)
```

Validated with: Python 3.12.12, pytest-gremlins 1.5.0b8, pytest-xdist 3.8.0, pytest-cov 7.0.0.

**Root cause of all-error baseline (prior run):** `--no-cov` requires `pytest-cov`. Without
it pytest exits code 4 (usage error), which pytest-gremlins maps to ERROR status. The
spike fixture does not declare `pytest-cov` as a dependency — the action's README must
document this requirement.

**Action design:** Keep `--gremlin-workers` as the parallelism input. It is the
pytest-gremlins native mechanism and avoids xdist's test-collection distribution, which
is orthogonal to mutation parallelism. Both work, but `--gremlin-workers` is the
documented interface.

Parallelism output format: `pytest-gremlins: Starting parallel execution with N workers`
followed by progress lines. BDD scenario should match this string.

### Q3: `actions/cache` permissions
**Decision:** No special `permissions:` block required. Default permissions (`contents: read`)
are sufficient for both restore and save. `actions: write` is NOT needed for cache operations.
Document in README: callers do not need to add a permissions block for caching.

### Q4: `@v1` floating tag lifecycle
**Decision:** Mutable floating tag. After each `v1.x.y` release:
```bash
git tag -f v1 v1.x.y
git push --force origin v1
```
This is the standard convention for GitHub Actions major versions. Users pin to `@v1`
and automatically get patch/minor updates.

### Q5: Source path discovery
**Decision:** pytest-gremlins does NOT auto-discover flat-layout source files (e.g., `mathlib.py`
at project root). It looks for: `--gremlin-targets` CLI option, `[tool.pytest-gremlins] paths`
in pyproject.toml, `[tool.setuptools]` package config, or a `src/` directory.

The spike fixture uses `[tool.pytest-gremlins] paths = ["mathlib.py"]` in pyproject.toml.
The action's README must document this requirement for callers whose source is not in `src/`.

### Q6: `cache: write` permission absent behavior
**Decision:** Warn and continue. The action emits `::warning::` and proceeds without
caching. Mutation testing succeeds; only the cache benefit is lost. This is better than
failing fast: the user can debug permissions separately without blocking CI.

### Q7: Canonical fixture mutant count
**9** gremlins total across 3 functions in `mathlib.py`.

The BDD Bootstrap scenario "All mutants are evaluated" must assert this exact count.

### Q8: Parallelism observation
With `--gremlin-workers=2`, output includes:
```
pytest-gremlins: Starting parallel execution with 2 workers
pytest-gremlins: Progress 1/9 ... Progress 9/9
```
The BDD scenario "Parallelism is active" asserts a line matching
`Starting parallel execution with \d+ workers` with value > 1.

### Q9: `if: always()` in composite actions
**Confirmed valid.** GitHub Actions runner evaluates step-level `if:` conditions in composite
actions identically to job-level steps. The save step runs even when a prior step exits non-zero.

### Pre-seeding IncrementalCache without two live CI runs

Run pytest-gremlins twice in the same CI job.

The IncrementalCache stores per-gremlin results in `.gremlins_cache/` keyed by content
hash. To validate the "warm cache skips unchanged gremlins" scenario without two sequential
workflow runs:

1. First invocation: `pytest --gremlins` — populates `.gremlins_cache/` for all 9 gremlins
2. Second invocation: `pytest --gremlins` (same working directory, no file changes) —
   IncrementalCache hits cause gremlins to be reported as skipped

This is reproducible within a single CI job and requires no external pre-seeding.
The test harness uses this pattern: run twice, assert the second run's log contains
cache-hit markers.

The alternative — uploading a pre-computed artifact via `actions/cache` save — requires
knowing the exact cache key format at test-authoring time. That's fragile. Two sequential
runs in one job is deterministic and self-contained.

### Matrix cache key scoping

**Decision:** Cache key includes `${{ env.pythonLocation }}` (set by `actions/setup-python`)
to prevent cross-Python-version cache collisions in matrix jobs. Falls back to OS-only
scope via `restore-keys` when `pythonLocation` is unset (callers who skip `actions/setup-python`
still get a warm cache rather than a miss).

## Open Questions Resolved

| Question | Decision |
|----------|----------|
| `cache: write` absent: warn or fail? | Warn and continue |
| `@v1` tag lifecycle: mutable or static? | Mutable floating tag |
| xdist `-n auto` for parallelism? | Works on Python 3.12 + b8, but keep `--gremlin-workers` (native mechanism) |
| Source auto-discovery for flat layout? | Requires `[tool.pytest-gremlins] paths` or `--gremlin-targets` |

## Recommended BDD Scenarios

The 7 Gherkin scenarios in the epic body (mikelane/pytest-gremlins#305) require updates
based on spike findings:

- **Mutant count assertion**: 9 (exact, from Q7)
- **Worker pattern**: `Starting parallel execution with \d+ workers` in output, value > 1
- **Parallelism input**: `workers: '2'` (maps to `--gremlin-workers=2`), NOT `parallel: 'true'`
- **Cache presence assertion**: `actions/cache` restore step returning HIT
- **Source discovery**: caller's pyproject.toml must configure `[tool.pytest-gremlins] paths`

## Separate Finding: Python 3.14 OperatorRegistry Bug

All 9 gremlins errored when the spike first ran on the system Python (3.14). The immediate
cause was `--no-cov` being unrecognized (no `pytest-cov`), but switching to Python 3.12
and installing `pytest-cov` resolved it. The 3.14 environment was not investigated further.

**Recommended action:** File a bug against pytest-gremlins to test against Python 3.14
and identify whether the `OperatorRegistry` failure is a real incompatibility or just the
missing `pytest-cov` masking a clean run.

## Deliverables Checklist

- [x] `action.yml` at repo root (GitHub Marketplace requirement)
- [x] `spike-fixture/` committed (canonical fixture with known mutant count: 9)
- [x] `docs/spikes/spike-3-actions-marketplace.md` (this document)
- [x] Q1–Q9 answered with decisions
- [x] xdist incompatibility discovered and documented (critical design correction)
- [x] Initial test harness scaffold — `features/`, behave runner, CI job stub (`.github/workflows/test.yml`)
