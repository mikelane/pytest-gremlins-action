"""Step definitions for pytest-gremlins action behavior BDD scenarios.

These steps invoke pytest-gremlins directly via subprocess against the
spike-fixture directory. No GitHub Actions runtime is needed for the red
phase — the action is a thin wrapper around pytest-gremlins, so we test
the underlying tool behavior directly.

NOTE: The `mutation-score` output written to $GITHUB_OUTPUT is only set inside
an Actions runner environment and is not verified by these local BDD scenarios.
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
_CACHE_DIR_NAME = '.gremlins_cache'

# Allowlist of environment keys passed to the pytest subprocess.
# Avoids leaking CI secrets (GITHUB_TOKEN, AWS_*, etc.) into the child process.
_SUBPROCESS_ENV_KEYS = {
    'PATH', 'HOME', 'TMPDIR', 'TEMP', 'TMP',
    'PYTHONPATH', 'VIRTUAL_ENV',
    'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING',
    'LANG', 'LC_ALL', 'LC_CTYPE',
    'USER', 'LOGNAME',
}


def _cache_dir(context):
    """Return the expected IncrementalCache directory path for the current scenario."""
    return os.path.join(context.fixture_dir, _CACHE_DIR_NAME)


def _copy_fixture(context):
    """Copy only the essential spike-fixture files into context.tmpdir.

    Copies mathlib.py, pyproject.toml, and tests/ — skipping .pytest_cache,
    .coverage.* and other ephemeral artefacts that interfere with pytest
    rootdir detection and coverage collection.
    """
    fixture_dest_dir = os.path.join(context.tmpdir, 'fixture')
    os.makedirs(fixture_dest_dir, exist_ok=True)
    for name in _FIXTURE_INCLUDES:
        source_path = os.path.join(context.fixture_src, name)
        destination_path = os.path.join(fixture_dest_dir, name)
        try:
            if os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
        except OSError as exc:
            raise RuntimeError(
                f'[pga-bdd] Failed to copy fixture item {name!r} '
                f'from {source_path!r} to {destination_path!r}: {exc}'
            ) from exc
    return fixture_dest_dir


def _run_pytest_gremlins(fixture_dir, extra_args=None, env_overrides=None):
    """Run pytest --gremlins against fixture_dir and return (combined_output, returncode, elapsed).

    Passes fixture_dir as both --rootdir and the positional test path so pytest
    picks up pyproject.toml as its ini file regardless of the caller's cwd.
    Uses an environment allowlist to avoid leaking CI secrets into the subprocess.
    """
    cmd = [
        sys.executable, '-m', 'pytest',
        '--gremlins',
        f'--rootdir={fixture_dir}',
        fixture_dir,
    ] + (extra_args or [])
    env = {k: v for k, v in os.environ.items() if k in _SUBPROCESS_ENV_KEYS}
    if env_overrides:
        env.update(env_overrides)
    start_time = time.monotonic()
    try:
        completed_process = subprocess.run(
            cmd,
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start_time
        partial_output = (exc.stdout or b'').decode('utf-8', errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        raise RuntimeError(
            f'[pga-bdd] pytest-gremlins timed out after {elapsed:.1f}s.\n'
            f'Command: {cmd}\n'
            f'Fixture: {fixture_dir}\n'
            f'Partial output:\n{partial_output}'
        ) from exc
    elapsed = time.monotonic() - start_time
    combined_output = completed_process.stdout + '\n' + completed_process.stderr
    return combined_output, completed_process.returncode, elapsed


# ---------------------------------------------------------------------------
# Given steps
# ---------------------------------------------------------------------------

@given('the canonical fixture project with {count:d} gremlins')
def step_fixture_with_count(context, count):
    context.expected_gremlin_count = count
    context.fixture_dir = _copy_fixture(context)


@given('a workflow using `uses: mikelane/pytest-gremlins-action@v1`')
def step_workflow_uses_action(context):
    # This step marks scenarios that exercise composite action behaviour.
    # extra_args is already initialised to [] by before_scenario in environment.py.
    pass


@given('the workflow has no extra inputs')
def step_workflow_no_extra_inputs(context):
    # Default action behaviour: parallel=true maps to -n auto (xdist).
    # cache=false locally (no actions/cache available), threshold=0.
    context.extra_args = ['-n', 'auto']


@given('the workflow has a threshold of {value:d}')
def step_workflow_threshold(context, value):
    # Threshold enforcement is composite action logic, not a pytest flag.
    # Use sequential mode + --gremlin-cache so coverage is collected and
    # cache entries are written even when the threshold gate fires.
    # (xdist workers report "No data was collected", which prevents cache
    # key resolution locally.)
    context.threshold = value
    context.extra_args = ['--gremlin-cache']


@given('a cold run has already populated the IncrementalCache')
def step_cold_run_populated_cache(context):
    # Merge context.extra_args so the cold run respects the action's parallelism
    # setting, then force-add --gremlin-cache (cache is the point of this step).
    extra_args_with_cache = list(context.extra_args)
    if '--gremlin-cache' not in extra_args_with_cache:
        extra_args_with_cache.append('--gremlin-cache')
    output, returncode, elapsed = _run_pytest_gremlins(
        context.fixture_dir,
        extra_args=extra_args_with_cache,
    )
    context.cold_output = output
    context.cold_elapsed = elapsed
    assert returncode == 0, f'Cold run failed (exit {returncode}):\n{output}'
    assert os.path.isdir(_cache_dir(context)), (
        f'Cold run did not create {_CACHE_DIR_NAME} at {_cache_dir(context)}'
    )


@given("the workflow has `parallel: 'false'`")
def step_workflow_parallel_false(context):
    context.extra_args = []  # no xdist, single-process


@given("the workflow has `cache: 'false'`")
def step_workflow_cache_false(context):
    # action.yml omits --gremlin-cache when cache='false'; the absence of the
    # flag is what we verify here (no cache dir created after the run).
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
    context.elapsed = elapsed
    # Simulate composite action threshold enforcement: parse the zapped
    # percentage and exit non-zero if it falls below context.threshold.
    threshold = getattr(context, 'threshold', 0)
    if returncode == 0 and threshold > 0:
        score_match = re.search(
            r'Zapped: \d+ gremlins \((\d+(?:\.\d+)?)%\)', output
        )
        if score_match and float(score_match.group(1)) < threshold:
            returncode = 1
    context.returncode = returncode


@when('the CI job runs again with no file changes')
def step_ci_job_runs_again(context):
    # Merge context.extra_args so the warm run uses the same parallelism
    # setting as the cold run, then force-add --gremlin-cache.
    extra_args_with_cache = list(context.extra_args)
    if '--gremlin-cache' not in extra_args_with_cache:
        extra_args_with_cache.append('--gremlin-cache')
    output, returncode, elapsed = _run_pytest_gremlins(
        context.fixture_dir,
        extra_args=extra_args_with_cache,
    )
    context.warm_output = output
    context.warm_returncode = returncode
    context.warm_elapsed = elapsed


@when('the mutation phase completes')
def step_mutation_phase_completes(context):
    # Locally "mutation phase completes" and "CI job runs" invoke the same
    # subprocess — the distinction matters in the composite action (where the
    # mutation phase is a discrete step), but both resolve to the same pytest
    # invocation in this simulation.
    step_ci_job_runs(context)


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
    assert 'pytest-gremlins mutation report' in context.output, (
        f'Expected mutation report header in output but got:\n{context.output}'
    )


@then('the step log contains a line matching "Starting parallel execution with {pattern} workers"')
def step_log_contains_parallel_line(context, pattern):
    # In the red phase pytest-gremlins 1.5.0 resolves xdist workers but the
    # output uses "N workers" where N is numeric — this step should PASS green.
    full_pattern = rf'Starting parallel execution with {pattern} workers'
    assert re.search(full_pattern, context.output), (
        f'Expected line matching r"{full_pattern}" in output but got:\n{context.output}'
    )


@then('the worker count is greater than 1')
def step_worker_count_greater_than_one(context):
    worker_count_match = re.search(r'Starting parallel execution with (\d+) workers', context.output)
    assert worker_count_match, (
        f'Could not find numeric worker count in output:\n{context.output}'
    )
    worker_count = int(worker_count_match.group(1))
    assert worker_count > 1, (
        f'Expected worker count > 1 for parallel execution, but got {worker_count}.'
    )


@then('the step exits non-zero')
def step_exits_nonzero(context):
    assert context.returncode != 0, (
        f'Expected non-zero exit code but got {context.returncode}.\nOutput:\n{context.output}'
    )


@then('the IncrementalCache directory is present after the run')
def step_cache_dir_present(context):
    cache = _cache_dir(context)
    assert os.path.isdir(cache), (
        f'Expected {_CACHE_DIR_NAME} to exist at {cache} but it was absent.'
    )
    # An empty cache directory is as useless as no cache at all — the warm-run
    # scenario depends on entries being present.  Assert at least one entry was
    # written so this step proves real work was cached, not just that mkdir ran.
    entries = list(os.scandir(cache))
    assert entries, (
        f'Expected {_CACHE_DIR_NAME} to contain at least one entry but it was empty: {cache}'
    )


@then('the warm run reports at least 1 cache hit')
def step_warm_run_cache_hit(context):
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
    assert not os.path.exists(_cache_dir(context)), (
        f'Expected {_CACHE_DIR_NAME} to be absent at {_cache_dir(context)} but it was present.'
    )
