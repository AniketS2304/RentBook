# Git Workflow & Commit Rules

## Frequent Commits on Fixes and Features
- **Commit promptly**: Whenever a feature, bug fix, or phase milestone is completed and passes all tests, commit immediately.
- **Do not accumulate uncommitted changes**: Never leave finished and verified work uncommitted across tasks or prompts.
- **Atomic commits**: Each commit should represent a cohesive change (e.g. auth, properties, units, tenants, rent, or a specific bug fix).
- **Conventional commits**: Use descriptive conventional commit messages:
  - `feat(...)`: new functionality or completed phase
  - `fix(...)`: bug fix or regression fix
  - `test(...)`: test additions or updates
  - `docs(...)`: documentation or architecture updates
  - `refactor(...)`: non-functional code improvements
- **Verify before committing**: Ensure tests pass and the repository is in a clean, working state before creating commits.
