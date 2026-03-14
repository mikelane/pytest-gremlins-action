"""Behave environment hooks."""

def before_scenario(context, scenario):
    if 'pending' in scenario.tags:
        scenario.skip('Pending — implement in BDD Bootstrap (issue #4)')
