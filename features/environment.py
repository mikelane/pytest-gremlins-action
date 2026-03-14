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


def after_scenario(context, scenario):
    if hasattr(context, 'tmpdir') and os.path.exists(context.tmpdir):
        shutil.rmtree(context.tmpdir, ignore_errors=True)
