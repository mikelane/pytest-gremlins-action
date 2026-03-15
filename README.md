# pytest-gremlins-action

GitHub Actions composite action for [pytest-gremlins](https://github.com/mikelane/pytest-gremlins) mutation testing.

## Features

- Run mutation testing in CI with one step
- Incremental caching across workflow runs (13x speedup on repeat runs)
- Score ratcheting — mutation score can only go up
- PR comments with mutation report and surviving mutations table
- Shields.io badge for README embedding

## Quick Start

```yaml
- uses: mikelane/pytest-gremlins-action@v1
```

## Full Example

```yaml
name: Mutation Testing
on: [pull_request]

jobs:
  mutants:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - uses: mikelane/pytest-gremlins-action@v1
        id: gremlins
        with:
          cache: 'true'
          parallel: 'true'

      - name: Show score
        run: echo "Mutation score: ${{ steps.gremlins.outputs.score }}%"
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `python-version` | `'3.12'` | Python version |
| `parallel` | `'true'` | Enable parallel mutation testing |
| `workers` | `''` | Worker count (empty = all cores) |
| `cache` | `'true'` | Enable incremental cache |
| `targets` | `''` | Source paths to mutate |
| `extra-args` | `''` | Additional pytest arguments |
| `ratchet-file` | `'.gremlins-score'` | Score threshold file |
| `pr-comment` | `'true'` | Post PR comment |

## Outputs

| Output | Description |
|--------|-------------|
| `score` | Mutation score (%) |
| `zapped` | Killed mutations |
| `survived` | Surviving mutations |
| `timeout` | Timed-out mutations |
| `total` | Total mutations |
| `pardoned` | Pardoned mutations |
| `passed` | `'true'` if score >= threshold |
| `badge-url` | Shields.io badge URL |

## Badge

Add to your README:

```markdown
![Mutation Score](https://img.shields.io/badge/mutation_score-85.7%25-brightgreen)
```

Or use the `badge-url` output dynamically.

## Permissions

| Permission | Why |
|-----------|-----|
| `contents: write` | Auto-commit ratchet score updates |
| `pull-requests: write` | Post PR comments |

## License

MIT
