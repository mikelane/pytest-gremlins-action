"""Behave environment hooks."""
import shutil
import tempfile
import os


def before_scenario(context, scenario):
    context.tmpdir = tempfile.mkdtemp(prefix='pga-bdd-')
    context.fixture_src = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'spike-fixture',
    )
    if not os.path.isdir(context.fixture_src):
        raise RuntimeError(
            f'[pga-bdd] fixture_src does not exist: {context.fixture_src!r}. '
            f'Expected spike-fixture/ alongside the features/ directory.'
        )
    # Ensure extra_args is always present; step defs overwrite it per scenario.
    context.extra_args = []
    # fixture_dir is set by the Given step that copies the fixture.  Initialise
    # to None so that any step relying on it before the Given runs fails with a
    # clear AttributeError instead of a cryptic KeyError or silent wrong path.
    context.fixture_dir = None


def after_scenario(context, scenario):
    if hasattr(context, 'tmpdir') and os.path.exists(context.tmpdir):
        try:
            shutil.rmtree(context.tmpdir)
        except OSError as exc:
            # Use scenario.name so multi-scenario runs can pinpoint which scenario
            # left a dangling tmpdir.
            print(  # noqa: T201 — behave captures this in its own output stream
                f'[pga-bdd] WARNING: failed to remove tmpdir {context.tmpdir!r} '
                f"after scenario {scenario.name!r}: {exc}"
            )
