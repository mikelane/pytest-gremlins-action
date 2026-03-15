"""Subprocess and fixture-copy helpers shared across step definition modules.

These are pure infrastructure utilities — no behave imports, no context coupling.
Keeping them here lets action_steps.py stay focused on step definitions only.
"""
import os
import shutil
import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# Constants
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


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def cache_dir(fixture_dir):
    """Return the expected IncrementalCache directory path for fixture_dir."""
    return os.path.join(fixture_dir, _CACHE_DIR_NAME)


def copy_fixture(fixture_src, tmpdir):
    """Copy only the essential spike-fixture files into tmpdir.

    Copies mathlib.py, pyproject.toml, and tests/ — skipping .pytest_cache,
    .coverage.* and other ephemeral artefacts that interfere with pytest
    rootdir detection and coverage collection.

    Returns the path to the copied fixture directory.
    """
    dest = os.path.join(tmpdir, 'fixture')
    os.makedirs(dest, exist_ok=True)
    for name in _FIXTURE_INCLUDES:
        src = os.path.join(fixture_src, name)
        dst = os.path.join(dest, name)
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        except OSError as exc:
            raise RuntimeError(
                f'[pga-bdd] Failed to copy fixture item {name!r} '
                f'from {src!r} to {dst!r}: {exc}'
            ) from exc
    return dest


def run_pytest_gremlins(fixture_dir, extra_args=None, env_overrides=None):
    """Run pytest --gremlins against fixture_dir.

    Passes fixture_dir as both --rootdir and the positional test path so pytest
    picks up pyproject.toml as its ini file regardless of the caller's cwd.
    Uses an environment allowlist to avoid leaking CI secrets into the subprocess.

    Returns (combined_output, returncode, elapsed).
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
        raw = exc.stdout or b''
        partial_output = raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else raw
        raise RuntimeError(
            f'[pga-bdd] pytest-gremlins timed out after {elapsed:.1f}s.\n'
            f'Command: {cmd}\n'
            f'Fixture: {fixture_dir}\n'
            f'Partial output:\n{partial_output}'
        ) from exc
    elapsed = time.monotonic() - start_time
    combined_output = completed_process.stdout + '\n' + completed_process.stderr
    return combined_output, completed_process.returncode, elapsed
