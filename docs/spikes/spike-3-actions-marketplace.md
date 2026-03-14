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
| Parallelism observable | Yes — `Starting parallel execution with 12 workers` seen with `-n auto` on a 12-core machine |

## Findings

### Q1: Composite action step-level `if:` conditions
**Decision:** Yes — composite action steps support `if:` identically to job steps.
`if: always()` on the cache-save step is valid per the GitHub Actions runner spec.
This is the critical pattern: cache must save even when threshold check fails (non-zero exit).

### Q2: xdist compatibility — re-validated on Python 3.12 with v1.5.0b8

**Revised decision:** The original incompatibility finding was against stable (≤1.4.x). v1.5.0 ships two-phase xdist integration, so `pytest --gremlins -n auto` works: xdist distributes the unit tests across workers in Phase 1, then pytest-gremlins runs mutation evaluation using the same worker count (via `ProcessPoolExecutor`) in Phase 2. All 9 fixture gremlins were zapped correctly.

Since the action targets pytest-gremlins ≥ 1.5.0, the incompatibility simply isn't there. The `parallel` input therefore maps to `-n auto`; callers need `pytest-xdist` installed. Setting `parallel: 'false'` drops the flag entirely and runs single-process.

Validated with: Python 3.12.12, pytest-gremlins 1.5.0b8, pytest-xdist 3.8.0, pytest-cov 7.0.0.

**Root cause of all-error baseline (prior run):** `--no-cov` requires `pytest-cov`. Without
it pytest exits code 4 (usage error), which pytest-gremlins maps to ERROR status. The
spike fixture does not declare `pytest-cov` as a dependency — the action's README must
document this requirement.

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

**Finding (Q1):** `pytest --gremlins -n auto` works. xdist distributes the 5 unit tests across workers; pytest-gremlins then runs its own parallel mutation phase (12 workers, matching the machine's CPU count). On a 2-core GitHub-hosted `ubuntu-latest` runner, `-n auto` resolves to 2 workers, so the feature file's `value > 1` assertion holds on any runner with at least 2 cores. All 9 gremlins zapped, exit code 0.

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
v1.5.0b4 added three discovery strategies — `project-name`, `setup.cfg`, and `importlib` — so installed packages and conventionally named source directories are found automatically. The spike fixture doesn't fit either case: `mathlib.py` is a flat-layout file whose name doesn't match the project (`spike-fixture`), so it still needs explicit config:

```toml
[tool.pytest-gremlins]
paths = ["mathlib.py"]
```

The action README should call this out for callers with non-conventional layouts.

### Q6: `cache: write` permission absent behavior
**Decision:** Warn and continue. The action emits `::warning::` and proceeds without
caching. Mutation testing succeeds; only the cache benefit is lost. This is better than
failing fast: the user can debug permissions separately without blocking CI.

### Q7: Canonical fixture mutant count
**9** gremlins total across 3 functions in `mathlib.py`.

The BDD Bootstrap scenario "All mutants are evaluated" must assert this exact count.

### Q8: Parallelism observation
With `-n auto` on a 12-core machine, the output includes:
```
pytest-gremlins: Starting parallel execution with 12 workers
pytest-gremlins: Progress 1/9 ... Progress 9/9
```
On a 2-core `ubuntu-latest` runner this will show 2 workers. The BDD scenario "Parallelism is active" should match `Starting parallel execution with \d+ workers` and check that the count is greater than 1, which holds on any multi-core runner.

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
The BDD step for "warm cache skips unchanged gremlins" must assert timing, not log content.
The observed ratio was 43% (3.55s warm / 8.17s cold), but a < 50% threshold is too tight for CI:
loaded `ubuntu-latest` runners vary by ±20–30%, which can narrow the ratio and flip the assertion.

Recommended BDD Bootstrap approach: assert `warm_time < 0.70 * cold_time` (warm must be at
least 30% faster than cold). This gives an 18-point buffer above the observed ratio. Alternatively,
tag the warm-cache scenario `@slow` and mark it non-blocking in CI — acceptable if timing variance
is unpredictable at the 9-gremlin fixture size. A larger fixture (30+ gremlins) would widen the
timing gap and make a tighter threshold reliable.

Run B verbatim outputs:

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
to prevent cross-Python-version cache collisions in matrix jobs. When `pythonLocation` is unset (caller skipped `actions/setup-python`), the restore-key
`gremlins-${{ runner.os }}-${{ env.pythonLocation }}-` expands to `gremlins-ubuntu-latest--`
and matches any cache entry for that OS regardless of Python version — effectively OS-only scope.
This is an accepted trade-off: callers who manage their own Python setup get a warm cache hit
(possibly from a different Python version) rather than a cold miss. The BDD Bootstrap should
verify this degrades gracefully rather than silently loading incompatible cache content.

## Open Questions Resolved

| Question | Decision |
|----------|----------|
| `cache: write` absent: warn or fail? | Warn and continue |
| `@v1` tag lifecycle: mutable or static? | Mutable floating tag |
| xdist `-n auto` for parallelism? | Works on Python 3.12 + b8; `parallel: 'true'` maps to `-n auto` (xdist) |
| Source auto-discovery for flat layout? | Requires `[tool.pytest-gremlins] paths` or `--gremlin-targets` |
| Canonical fixture mutant count? | 9 |
| Parallelism log format? | `Starting parallel execution with \d+ workers`; BDD scenario asserts count > 1 |
| `if: always()` ordering? | `always()` must be first — `if: always() && inputs.cache == 'true'`; deferred to BDD Bootstrap for live validation |

## Recommended BDD Scenarios

The 7 Gherkin scenarios in the epic body (mikelane/pytest-gremlins#305) need a few updates based on what the spike found. Mutant count is 9 — assert that exactly. The parallelism scenario should match the log line `Starting parallel execution with \d+ workers` and check the count is greater than 1; on any multi-core runner that holds. The input to exercise is `parallel: 'true'`, which passes `-n auto` to pytest (callers must have `pytest-xdist` installed). The cache scenario should confirm the `actions/cache` restore step returns a HIT on the second run. Source discovery scenarios should set `[tool.pytest-gremlins] paths` in the fixture's pyproject.toml — auto-discovery won't find flat-layout files unless the module name matches the project name.

## Separate Finding: Python 3.14 OperatorRegistry Bug

All 9 gremlins errored when the spike first ran on the system Python (3.14). The immediate
cause was `--no-cov` being unrecognized (no `pytest-cov`), but switching to Python 3.12
and installing `pytest-cov` resolved it. The 3.14 environment was not investigated further.

**Recommended action:** File a bug against pytest-gremlins to test against Python 3.14
and identify whether the `OperatorRegistry` failure is a real incompatibility or just the
missing `pytest-cov` masking a clean run.

## Deliverables Checklist

- [x] `action.yml` at repo root (GitHub Marketplace requirement) — `mutation-score` output is a scaffold stub; score capture deferred to BDD Bootstrap
- [x] `spike-fixture/` committed (canonical fixture with known mutant count: 9)
- [x] `docs/spikes/spike-3-actions-marketplace.md` (this document)
- [x] Q1–Q9 answered with decisions
- [x] xdist compatibility re-validated against v1.5.0b8 — works; Q2 reversed
- [x] BDD scaffold — `features/action_behavior.feature` (7 scenarios, all 7 `@pending`), `features/environment.py`, `features/steps/pending_steps.py`, `.github/workflows/test.yml`; `behave --dry-run` exits 0
