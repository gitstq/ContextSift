# Contributing to ContextSift

Thanks for your interest in improving ContextSift! This project is zero-dependency and offline-first, so contributions should keep those two properties intact.

## Ground rules

- **No runtime dependencies.** Contributions must use only the Python standard library.
- **Determinism.** Same input + same config must always produce the same output.
- **Tests required.** Every behavior change needs a corresponding unit test.

## Development setup

```bash
git clone https://github.com/gitstq/ContextSift.git
cd ContextSift
python3 -m unittest discover -s tests -v
```

No install step is needed — the package runs directly from the source tree.

## Commit convention

We follow the [Angular commit convention](https://www.conventionalcommits.org/):

- `feat:` a new feature
- `fix:` a bug fix
- `docs:` documentation only
- `refactor:` code change that neither fixes a bug nor adds a feature
- `test:` adding or fixing tests
- `chore:` tooling / build changes

Example: `feat: add zip-based profile import`

## Pull request checklist

- [ ] All unit tests pass (`python3 -m unittest discover -s tests`)
- [ ] New behavior has unit-test coverage
- [ ] README updated if behavior or CLI changed
- [ ] Commit messages follow the convention above

## Reporting issues

Please include: Python version, OS, a minimal reproduction, and the expected vs. actual output.
