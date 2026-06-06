# Contributing to WDYAW

Thank you for considering a contribution. This project follows standard open-source practices.

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports, feature requests, and questions
- Include a minimal reproduction case for bugs
- Specify your Python version and operating system

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run the test suite: `pytest`
5. Ensure all tests pass and coverage remains >= 95%
6. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/WDYAW.git
cd WDYAW

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=wdyaw --cov-report=term-missing
```

### Code Standards

- Follow PEP 8
- Use type hints (built-in generics: `list`, `dict`, `tuple`)
- All functions must have docstrings
- Maintain test coverage >= 95%
- No `typing.Dict`, `typing.List`, or `typing.Tuple` — use built-in generics

### Testing Guidelines

- Every bug fix must include a regression test
- Every new feature must include tests
- Tests should be deterministic (no network calls, no randomness without seeds)
- Use pytest fixtures and parametrization where appropriate

### Commit Messages

Follow conventional commits:

```
feat: add new P04 failure pattern detection
fix: correct regex for apostrophe handling
docs: update TCRTE interview examples
test: add coverage for whitespace-only components
refactor: extract generic pattern detector
```

### Skill Changes

If modifying `SKILL.md`:

- Test the skill with at least one agent (OpenCode, Claude Code, or Cursor)
- Ensure the skill still activates on correct triggers
- Ensure the skill does not activate on negative triggers
- Update the version in `SKILL.md` frontmatter if behavior changes

## Release Process

See [PUBLISHING.md](PUBLISHING.md) for maintainer release instructions.
