"""Pending step definitions — filled in during BDD Bootstrap (issue #4)."""
from behave import given, when, then

# These steps are stubs. BDD Bootstrap will implement them.
# Scenarios tagged @pending will be skipped by behave by default.

@given('the canonical fixture project with {count:d} gremlins')
def step_fixture_with_count(context, count):
    raise NotImplementedError('Pending — implement in BDD Bootstrap')

@given('a workflow using `uses: mikelane/pytest-gremlins-action@v1`')
def step_workflow_uses_action(context):
    raise NotImplementedError('Pending — implement in BDD Bootstrap')

@given('the workflow has a threshold set above the fixture\'s mutation score')
def step_threshold_above_score(context):
    raise NotImplementedError('Pending — implement in BDD Bootstrap')

@when('the mutation phase completes')
def step_mutation_phase_completes(context):
    raise NotImplementedError('Pending — implement in BDD Bootstrap')

@then('the step exits non-zero')
def step_exits_nonzero(context):
    raise NotImplementedError('Pending — implement in BDD Bootstrap')

@then('the job is marked failed')
def step_job_marked_failed(context):
    raise NotImplementedError('Pending — implement in BDD Bootstrap')
