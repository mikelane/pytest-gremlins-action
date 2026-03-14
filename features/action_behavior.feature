Feature: pytest-gremlins GitHub Actions composite action

  Background:
    Given the canonical fixture project with 9 gremlins
    And a workflow using `uses: mikelane/pytest-gremlins-action@v1`

  @pending
  Scenario: All mutants are evaluated with no extra configuration

  @pending
  Scenario: Parallelism is active with no extra configuration

  @pending
  Scenario: Cache is saved when threshold failure occurs

  @pending
  Scenario: Warm cache skips unchanged gremlins on the next run

  @pending
  Scenario: Opt-out parallelism

  @pending
  Scenario: Opt-out caching

  Scenario: Threshold enforcement
    Given the workflow has a threshold set above the fixture's mutation score
    When the mutation phase completes
    Then the step exits non-zero
    And the job is marked failed
