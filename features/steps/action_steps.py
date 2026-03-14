"""Step definitions for pytest-gremlins action behavior BDD scenarios.

These steps invoke pytest-gremlins directly via subprocess against the
spike-fixture directory. No GitHub Actions runtime is needed for the red
phase — the action is a thin wrapper around pytest-gremlins, so we test
the underlying tool behavior directly.

NOTE: The `mutation-score` output written to $GITHUB_OUTPUT cannot be tested
locally because the composite action step writes it only inside an Actions
runner environment. Scenarios that depend on $GITHUB_OUTPUT are tagged
@ci-only and are excluded from local behave runs.
"""
import os
import re
import shutil
import subprocess
import sys
import time

from behave import given, when, then


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FIXTURE_INCLUDES = ('mathlib.py', 'pyproject.toml', 'tests')


def _copy_fixture(context):
    """Copy only the essential spike-fixture files into context.tmpdir.

    Copies mathlib.py, pyproject.toml, and tests/ — skipping .pytest_cache,
    .coverage.* and other ephemeral artefacts that interfere with pytest
    rootdir detection and coverage collection.
    """
    dest = os.path.join(context.tmpdir, 'fixture')
    os.makedirs(dest, exist_ok=True)
    for name in _FIXTURE_INCLUDES:
        src = os.path.join(context.fixture_src, name)
        dst = os.path.join(dest, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    return dest


def _run_pytest_gremlins(fixture_dir, extra_args=None, env_overrides=None):
    """Run pytest --gremlins against fixture_dir and return (output, returncode, elapsed).

    Passes fixture_dir as both --rootdir and the positional test path so pytest
    picks up pyproject.toml as its ini file regardless of the caller's cwd.
    """
    cmd = [
        sys.executable, '-m', 'pytest',
        '--gremlins',
        f'--rootdir={fixture_dir}',
        fixture_dir,
    ] + (extra_args or [])
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    t0 = time.monotonic()
    result = subprocess.run(
        cmd,
        cwd=fixture_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    elapsed = time.monotonic() - t0
    output = result.stdout + result.stderr
    return output, result.returncode, elapsed


# ---------------------------------------------------------------------------
# Given steps
# ---------------------------------------------------------------------------

@given('the canonical fixture project with {count:d} gremlins')
def step_fixture_with_count(context, count):
    context.expected_gremlin_count = count
    context.fixture_dir = _copy_fixture(context)


@given('a workflow using `uses: mikelane/pytest-gremlins-action@v1`')
def step_workflow_uses_action(context):
    # Records that we are simulating the action's behaviour locally.
    context.extra_args = []
    context.threshold = None
    context.parallel = True
    context.cache = False


@given('the workflow has no extra inputs')
def step_workflow_no_extra_inputs(context):
    # Default action behaviour: parallel=true maps to -n auto (xdist).
    # cache=false locally (no actions/cache available), threshold=0.
    context.extra_args = ['-n', 'auto']


@given('the workflow has a threshold of {value:d}')
def step_workflow_threshold(context, value):
    context.threshold = value
    # pytest-gremlins has no --gremlin-threshold flag — threshold enforcement
    # is composite action logic, not a pytest flag.  Run with caching so the
    # cache-presence assertion can be checked after the threshold step; the
    # red-phase failure is that pytest exits 0 (100% score) because the action
    # has not yet implemented the score-vs-threshold comparison and non-zero exit.
    context.extra_args = ['-n', 'auto', '--gremlin-cache']


@given('a cold run has already populated the IncrementalCache')
def step_cold_run_populated_cache(context):
    output, returncode, elapsed = _run_pytest_gremlins(
        context.fixture_dir,
        extra_args=['-n', 'auto', '--gremlin-cache'],
    )
    context.cold_output = output
    context.cold_elapsed = elapsed
    assert returncode == 0, f'Cold run failed (exit {returncode}):\n{output}'
    cache_dir = os.path.join(context.fixture_dir, '.gremlins_cache')
    assert os.path.isdir(cache_dir), (
        f'Cold run did not create .gremlins_cache at {cache_dir}'
    )


@given("the workflow has `parallel: 'false'`")
def step_workflow_parallel_false(context):
    context.extra_args = []  # no xdist, single-process


@given("the workflow has `cache: 'false'`")
def step_workflow_cache_false(context):
    context.extra_args = ['-n', 'auto']  # xdist but cache NOT enabled


# ---------------------------------------------------------------------------
# When steps
# ---------------------------------------------------------------------------

@when('the CI job runs')
def step_ci_job_runs(context):
    output, returncode, elapsed = _run_pytest_gremlins(
        context.fixture_dir,
        extra_args=context.extra_args,
    )
    context.output = output
    context.returncode = returncode
    context.elapsed = elapsed


@when('the CI job runs again with no file changes')
def step_ci_job_runs_again(context):
    output, returncode, elapsed = _run_pytest_gremlins(
        context.fixture_dir,
        extra_args=['-n', 'auto', '--gremlin-cache'],
    )
    context.warm_output = output
    context.warm_returncode = returncode
    context.warm_elapsed = elapsed


@when('the mutation phase completes')
def step_mutation_phase_completes(context):
    output, returncode, elapsed = _run_pytest_gremlins(
        context.fixture_dir,
        extra_args=context.extra_args,
    )
    context.output = output
    context.returncode = returncode
    context.elapsed = elapsed


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------

@then('all {count:d} fixture gremlins are evaluated')
def step_all_gremlins_evaluated(context, count):
    # pytest-gremlins 1.5.0 progress format: "pytest-gremlins: Progress N/total"
    pattern = rf'pytest-gremlins: Progress {count}/{count}'
    assert re.search(pattern, context.output), (
        f'Expected "{pattern}" in output but got:\n{context.output}'
    )


@then('the step log includes "Zapped: {count:d} gremlins"')
def step_log_includes_zapped(context, count):
    expected = f'Zapped: {count} gremlins'
    assert expected in context.output, (
        f'Expected "{expected}" in output but got:\n{context.output}'
    )


@then('the step log includes a mutation score summary')
def step_log_includes_score_summary(context):
    # The summary block always contains the separator line and Zapped/Survived.
    assert 'pytest-gremlins mutation report' in context.output, (
        f'Expected mutation report header in output but got:\n{context.output}'
    )


@then('the step log contains a line matching "Starting parallel execution with {pattern} workers"')
def step_log_contains_parallel_line(context, pattern):
    # The actual output uses "auto" not a digit count, so this assertion will
    # fail in the red phase: the regex \d+ does not match "auto".
    full_pattern = rf'Starting parallel execution with {pattern} workers'
    assert re.search(full_pattern, context.output), (
        f'Expected line matching r"{full_pattern}" in output but got:\n{context.output}'
    )


@then('the worker count is greater than 1')
def step_worker_count_greater_than_one(context):
    # Requires the parallel line to expose a numeric worker count.
    # pytest-gremlins 1.4.0 prints "auto" not a number — this step will fail
    # in the red phase until the plugin surfaces the resolved count.
    match = re.search(r'Starting parallel execution with (\d+) workers', context.output)
    assert match, (
        f'Could not find numeric worker count in output:\n{context.output}'
    )
    assert int(match.group(1)) > 1, (
        f'Worker count {match.group(1)} is not greater than 1'
    )


@then('the job exits non-zero')
def step_job_exits_nonzero(context):
    assert context.returncode != 0, (
        f'Expected non-zero exit code but got {context.returncode}.\nOutput:\n{context.output}'
    )


@then('the IncrementalCache directory is present after the run')
def step_cache_dir_present(context):
    cache_dir = os.path.join(context.fixture_dir, '.gremlins_cache')
    assert os.path.isdir(cache_dir), (
        f'Expected .gremlins_cache to exist at {cache_dir} but it was absent.'
    )


@then('the warm run reports at least 1 cache hit')
def step_warm_run_cache_hit(context):
    # Red-phase failure: pytest-gremlins' IncrementalCache keys entries by
    # (source hash + coverage hash). With no coverage data collected (xdist
    # workers emit "No data was collected"), every gremlin is a cache miss.
    # This step will pass (GREEN) once the composite action configures
    # pytest-cov so that coverage data is collected and cache keys resolve.
    match = re.search(r'Cache: (\d+) hits', context.warm_output)
    assert match, (
        f'Could not find cache hit line in output:\n{context.warm_output}'
    )
    hits = int(match.group(1))
    assert hits > 0, (
        f'Expected at least 1 cache hit but got {hits}.\n'
        f'Output:\n{context.warm_output}'
    )


@then('the step log does not contain "Starting parallel execution with"')
def step_log_no_parallel(context):
    assert 'Starting parallel execution with' not in context.output, (
        f'Found unexpected parallel execution line in output:\n{context.output}'
    )


@then('the IncrementalCache directory is absent after the run')
def step_cache_dir_absent(context):
    cache_dir = os.path.join(context.fixture_dir, '.gremlins_cache')
    assert not os.path.exists(cache_dir), (
        f'Expected .gremlins_cache to be absent at {cache_dir} but it was present.'
    )


@then('the step exits non-zero')
def step_exits_nonzero(context):
    assert context.returncode != 0, (
        f'Expected non-zero exit code but got {context.returncode}.\nOutput:\n{context.output}'
    )


@then('the job is marked failed')
def step_job_marked_failed(context):
    # Locally "job failed" means the pytest process exited non-zero.
    # The GitHub Actions job-level failure (red X in the UI) cannot be
    # asserted without an Actions runner.
    assert context.returncode != 0, (
        f'Expected non-zero exit code (job failure) but got {context.returncode}.\n'
        f'Output:\n{context.output}'
    )
