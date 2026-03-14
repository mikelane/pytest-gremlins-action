Feature: pytest-gremlins GitHub Actions composite action

  Background:
    Given the canonical fixture project with 9 gremlins
    And a workflow using `uses: mikelane/pytest-gremlins-action@v1`

  Scenario: All mutants are evaluated with no extra configuration
    And the workflow has no extra inputs
    When the CI job runs
    Then all 9 fixture gremlins are evaluated
    And the step log includes "Zapped: 9 gremlins"
    And the step log includes a mutation score summary

  Scenario: Parallelism is active with no extra configuration
    And the workflow has no extra inputs
    When the CI job runs
    Then the step log contains a line matching "Starting parallel execution with \d+ workers"
    And the worker count is greater than 1

  Scenario: Cache is saved when threshold failure occurs
    And the workflow has a threshold of 101
    When the CI job runs
    Then the job exits non-zero
    And the IncrementalCache directory is present after the run

  Scenario: Warm cache skips unchanged gremlins on the next run
    And a cold run has already populated the IncrementalCache
    When the CI job runs again with no file changes
    Then the warm run reports at least 1 cache hit

  Scenario: Opt-out parallelism
    And the workflow has `parallel: 'false'`
    When the CI job runs
    Then the step log does not contain "Starting parallel execution with"

  Scenario: Opt-out caching
    And the workflow has `cache: 'false'`
    When the CI job runs
    Then the IncrementalCache directory is absent after the run

  Scenario: Threshold enforcement
    And the workflow has a threshold of 101
    When the mutation phase completes
    Then the step exits non-zero
    And the job is marked failed
