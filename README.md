# pytest-gremlins-action

Drop [pytest-gremlins](https://github.com/mikelane/pytest-gremlins) mutation testing into your CI pipeline in one step.

## Usage

Minimal — fail the job if fewer than 80% of gremlins are zapped:

```yaml
- name: Mutation testing
  uses: mikelane/pytest-gremlins-action@v1
  with:
    threshold: '80'
```

Full workflow:

```yaml
name: CI
on: [push, pull_request]

jobs:
  mutation-testing:
    runs-on: ubuntu-latest
    permissions:
      actions: write  # needed for cache read/write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pytest pytest-gremlins pytest-xdist
      - uses: mikelane/pytest-gremlins-action@v1
        with:
          parallel: 'true'
          cache: 'true'
          threshold: '80'
          args: 'tests/'
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `parallel` | `'true'` | Run gremlins in parallel via pytest-xdist (`-n auto`). Set to `'false'` for sequential mode. |
| `cache` | `'true'` | Skip unchanged gremlins on subsequent runs using IncrementalCache. Requires `actions: write` permission. |
| `threshold` | `'0'` | Minimum mutation score (0–100). The step exits non-zero if the score falls below this value. `'0'` disables the gate. |
| `args` | `''` | Extra arguments forwarded verbatim to pytest (e.g. `tests/unit`). |

## Outputs

| Output | Description |
|--------|-------------|
| `mutation-score` | Mutation score as a numeric string, e.g. `"87.5"`. |

## Prerequisites

`pytest-gremlins` must be installed in the Python environment before this action runs. When `parallel` is `true` (the default), `pytest-xdist` is also required — omitting it will cause the run to fail with a missing plugin error.
