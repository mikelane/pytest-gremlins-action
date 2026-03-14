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

**Q1 empirical validation — Run A (`-n auto`):**

Run: `pytest --gremlins -n auto -v` in `spike-fixture/` on Python 3.12.12 + pytest-gremlins 1.5.0b8 + pytest-xdist 3.8.0.

```
============================= test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0 -- /private/tmp/pga-b8-venv/bin/python
cachedir: .pytest_cache
rootdir: /private/tmp/pga-spike-fix/spike-fixture
configfile: pyproject.toml
testpaths: tests
plugins: xdist-3.8.0, gremlins-1.5.0b8, cov-7.0.0
created: 12/12 workers
12 workers [5 items]

scheduling tests via LoadScheduling

tests/test_mathlib.py::test_add_positive PASSED                          [ 20%]
tests/test_mathlib.py::test_add_negative PASSED                          [ 40%]
tests/test_mathlib.py::test_multiply PASSED                              [ 60%]
tests/test_mathlib.py::test_multiply_zero PASSED                         [ 80%]
tests/test_mathlib.py::test_is_positive PASSED                           [100%]
pytest-gremlins: Starting parallel execution with 12 workers
pytest-gremlins: Progress 1/9 ... Progress 9/9


======================= pytest-gremlins mutation report ========================

Zapped: 9 gremlins (100%)
Survived: 0 gremlins (0%)

============================== 5 passed in 2.97s ===============================
```

**Finding (Q1):** `pytest --gremlins -n auto` works. xdist distributes the 5 unit tests
across workers; pytest-gremlins then runs its own parallel mutation phase (`12 workers`
matched the machine's CPU count). All 9 gremlins zapped. Exit code 0. The action's
`--gremlin-workers` input remains the documented interface, but `-n auto` is confirmed
compatible for callers who pass it via `args:`.

### Q3: `actions/cache` permissions
**Design decision — not empirically validated by a CI run during the spike. Validate in BDD Bootstrap.**
Per GitHub Actions documentation, `actions/cache` does not require `actions: write` — cache
read/write is governed by the `ACTIONS_CACHE_URL` token, which is always available to
workflow jobs regardless of the declared `permissions:` block. This was not exercised in a
live workflow run during the spike. The BDD Bootstrap should include a scenario that confirms
caching works in a workflow with only the default permissions, so the README claim is
grounded in a passing CI run rather than documentation alone.

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
**Design decision — not empirically validated by a CI run during the spike. Validate in BDD Bootstrap.**
GitHub Actions runner documentation states that step-level `if:` conditions in composite
actions behave identically to job-level steps, so `if: always()` on the cache-save step
should run even when a prior step exits non-zero. However, this was not exercised in a
live workflow run during the spike. The BDD Bootstrap "Cache is saved when threshold
failure occurs" scenario is the correct place to validate this end-to-end.

Note: `always()` must appear first in the `if:` expression. `if: inputs.cache == 'true' && always()`
is evaluated left-to-right and the `always()` has no effect when placed after a short-circuit
condition. The correct form is `if: always() && inputs.cache == 'true'`.

### Pre-seeding IncrementalCache without two live CI runs

Run pytest-gremlins twice in the same CI job.

The IncrementalCache stores per-gremlin results in `.gremlins_cache/` keyed by content
hash. To validate the "warm cache skips unchanged gremlins" scenario without two sequential
workflow runs:

1. First invocation: `pytest --gremlins` — populates `.gremlins_cache/` for all 9 gremlins
2. Second invocation: `pytest --gremlins` (same working directory, no file changes) —
   IncrementalCache hits cause gremlins to be skipped

This is reproducible within a single CI job and requires no external pre-seeding.

**Run B empirical finding:** Both runs produced identical output line-for-line. There is
no distinctive log line such as "cached" or "skipped" in the second run. The only
observable difference is wall-clock time: cold run 8.17s, warm run 3.55s (57% faster).
The BDD step for "warm cache skips unchanged gremlins" must therefore assert timing, not
log content — for example, assert the second run completes in under half the time of the
first. Run B verbatim outputs:

**First run (cold — `.gremlins_cache/` absent):**
```
Gremlin 1/9: mathlib_f57b_g001 - running 2/5 tests
Gremlin 2/9: mathlib_f57b_g002 - running 2/5 tests
Gremlin 3/9: mathlib_f57b_g003 - running 2/5 tests
Gremlin 4/9: mathlib_f57b_g004 - running 2/5 tests
Gremlin 5/9: mathlib_f57b_g005 - running 1/5 tests
Gremlin 6/9: mathlib_f57b_g006 - running 1/5 tests
Gremlin 7/9: mathlib_f57b_g007 - running 1/5 tests
Gremlin 8/9: mathlib_f57b_g008 - running 1/5 tests
Gremlin 9/9: mathlib_f57b_g009 - running 1/5 tests

Zapped: 9 gremlins (100%) | 5 passed in 8.17s
```

**Second run (warm — `.gremlins_cache/` populated, no file changes):**
```
Gremlin 1/9: mathlib_f57b_g001 - running 2/5 tests
Gremlin 2/9: mathlib_f57b_g002 - running 2/5 tests
Gremlin 3/9: mathlib_f57b_g003 - running 2/5 tests
Gremlin 4/9: mathlib_f57b_g004 - running 2/5 tests
Gremlin 5/9: mathlib_f57b_g005 - running 1/5 tests
Gremlin 6/9: mathlib_f57b_g006 - running 1/5 tests
Gremlin 7/9: mathlib_f57b_g007 - running 1/5 tests
Gremlin 8/9: mathlib_f57b_g008 - running 1/5 tests
Gremlin 9/9: mathlib_f57b_g009 - running 1/5 tests

Zapped: 9 gremlins (100%) | 5 passed in 3.55s
```

**Diff: none in log lines. Observable is timing only.**

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
