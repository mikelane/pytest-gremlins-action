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

### Q2: xdist incompatibility — use `--gremlin-workers` instead
**Decision:** pytest-gremlins is **incompatible with pytest-xdist test distribution**.
Running `pytest --gremlins -n 2` exits immediately with:
```
Exit: pytest-gremlins is incompatible with pytest-xdist test distribution.
Remove -n from your invocation (or from addopts) when running mutation tests.
Use --gremlin-workers=N to parallelise mutation execution instead.
```
The action input must be `workers` (mapped to `--gremlin-workers=N`), NOT `parallel` mapped
to xdist `-n auto`. This is a critical correction to the original action design.

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

## Open Questions Resolved

| Question | Decision |
|----------|----------|
| `cache: write` absent: warn or fail? | Warn and continue |
| `@v1` tag lifecycle: mutable or static? | Mutable floating tag |
| xdist `-n auto` for parallelism? | NO — use `--gremlin-workers=N` instead; xdist is incompatible |
| Source auto-discovery for flat layout? | Requires `[tool.pytest-gremlins] paths` or `--gremlin-targets` |

## Recommended BDD Scenarios

The 7 Gherkin scenarios in the epic body (mikelane/pytest-gremlins#305) require updates
based on spike findings:

- **Mutant count assertion**: 9 (exact, from Q7)
- **Worker pattern**: `Starting parallel execution with \d+ workers` in output, value > 1
- **Parallelism input**: `workers: '2'` (maps to `--gremlin-workers=2`), NOT `parallel: 'true'`
- **Cache presence assertion**: `actions/cache` restore step returning HIT
- **Source discovery**: caller's pyproject.toml must configure `[tool.pytest-gremlins] paths`

## Deliverables Checklist

- [x] `action.yml` at repo root (GitHub Marketplace requirement)
- [x] `spike-fixture/` committed (canonical fixture with known mutant count: 9)
- [x] `docs/spikes/spike-3-actions-marketplace.md` (this document)
- [x] Q1–Q9 answered with decisions
- [x] xdist incompatibility discovered and documented (critical design correction)
- [ ] Initial test harness scaffold — deferred to BDD Bootstrap issue #4
