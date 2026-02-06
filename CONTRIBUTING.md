# Contributing / Workflow (Mate Academy style)

## Branching
- `main` - stable release
- `develop` - integration branch
- feature branches: `feature/<short-task-name>`

## Pull Requests
- PRs go into `develop`
- Final PR: `develop -> main`
- Enable branch protection:
  - Require PR
  - Require **2 approvals**
  - Require CI checks (pytest + flake8)

## Commit naming examples
- `Init project`
- `Add cinema models`
- `Implement movies endpoints`
- `Add JWT auth`
- `Add throttling`
- `Add Swagger docs`
- `Add tests for movies`
- `Fix validation for tickets`
