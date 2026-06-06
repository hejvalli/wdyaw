# Publishing Guide

This document covers how to publish WDYAW to all supported platforms.

## Platforms

| Platform | Purpose | How Users Install |
|----------|---------|-------------------|
| **PyPI** | Python package distribution | `pip install wdyaw` |
| **skills.sh / skills.re** | Agent skill registry (planned) | `npx skills add hejvalli/WDYAW` |
| **OpenCode** | OpenCode agent skills | Auto-discovered from repo or `~/.config/opencode/skills/` |
| **Claude Code** | Claude Code skills | `~/.claude/skills/wdyaw/` |
| **OpenAI Codex** | Codex skills | `~/.codex/skills/wdyaw/` |
| **GitHub Releases** | Versioned source archives | Download from releases page |

---

## PyPI (Python Package Index)

### Prerequisites

- PyPI account: [pypi.org](https://pypi.org)
- API token stored in `~/.pypirc` or GitHub repository secrets

### Manual Release

```bash
# 1. Ensure tests pass
pytest --cov=wdyaw --cov-report=term-missing

# 2. Update version in pyproject.toml and __init__.py
# 3. Update CHANGELOG.md
# 4. Commit and tag
git add -A
git commit -m "release: v0.1.0"
git tag v0.1.0
git push origin main --tags

# 5. Build and upload
python -m build
twine upload dist/*
```

### Automated Release (GitHub Actions)

The repository includes a GitHub Actions workflow (`.github/workflows/release.yml`) that automatically publishes to PyPI when you push a tag matching `v*.*.*`.

**Setup:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add secret `PYPI_API_TOKEN` with your PyPI API token
3. Push a tag: `git tag v0.1.0 && git push origin v0.1.0`
4. The workflow builds and uploads automatically

---

## skills.sh / skills.re (Planned)

> **Not yet published.** This section documents the planned process for submitting to the skills.sh registry once ready.

### Prerequisites

- Public GitHub repository
- Valid `SKILL.md` with proper frontmatter

### Submit (Future)

1. Go to [skills.re/submit](https://skills.re/submit)
2. Paste your repository URL: `https://github.com/hejvalli/WDYAW`
3. The registry detects all `SKILL.md` files automatically
4. Review the preview and validation results
5. Click Submit

### Update

To release a new version:
1. Update `SKILL.md` content
2. Bump version in `SKILL.md` frontmatter (`metadata.version`)
3. Commit and push to main
4. Re-submit via the website

Each submission creates an immutable snapshot. Old versions remain available.

---

## Vercel Skills CLI

Users can install your skill directly from GitHub:

```bash
# Install all skills from the repo
npx skills add hejvalli/WDYAW

# Install specific skill
npx skills add hejvalli/WDYAW --skill wdyaw

# Install globally
npx skills add hejvalli/WDYAW -g
```

The CLI discovers skills in these locations:
- Root directory (`SKILL.md`)
- `skills/` subdirectory
- `.claude/skills/` subdirectory
- `.agents/skills/` subdirectory
- And many more agent-specific paths

WDYAW places `SKILL.md` in the root (`wdyaw/SKILL.md`), which is discovered automatically.

---

## OpenCode

OpenCode discovers skills from multiple locations:

```
# Project-level
.opencode/skills/wdyaw/SKILL.md
.claude/skills/wdyaw/SKILL.md
.agents/skills/wdyaw/SKILL.md

# Global
~/.config/opencode/skills/wdyaw/SKILL.md
~/.claude/skills/wdyaw/SKILL.md
~/.agents/skills/wdyaw/SKILL.md
```

### Install for Project

```bash
cp -r wdyaw .opencode/skills/
```

### Install Globally

```bash
cp -r wdyaw ~/.config/opencode/skills/
```

### Requirements

- Directory name **must match** `name` field in `SKILL.md` frontmatter
- `SKILL.md` must be all uppercase
- Frontmatter must include `name` and `description`
- Name must be lowercase alphanumeric with hyphens only

---

## Claude Code

Claude Code uses the same skill format as OpenCode:

```bash
# Install globally
mkdir -p ~/.claude/skills
cp -r wdyaw ~/.claude/skills/

# Or install to current project
mkdir -p .claude/skills
cp -r wdyaw .claude/skills/
```

Restart Claude Code after installation. The skill will be available via `/wdyaw` or automatic activation based on the description.

---

## OpenAI Codex

Codex discovers skills from `.agents/skills/`:

```bash
# Install globally
mkdir -p ~/.codex/skills
cp -r wdyaw ~/.codex/skills/

# Or install to current project
mkdir -p .agents/skills
cp -r wdyaw .agents/skills/
```

Invoke with `$wdyaw` or let Codex match based on the skill description.

---

## GitHub Releases

GitHub Releases are created automatically by the release workflow when you push a version tag.

### Manual Release

```bash
# Create and push tag
git tag v0.1.0
git push origin v0.1.0

# GitHub Actions will:
# 1. Run tests
# 2. Build source distribution
# 3. Build wheel
# 4. Create GitHub Release with artifacts
# 5. Publish to PyPI
```

### Release Checklist

Before creating a release:

- [ ] All tests pass (`pytest`)
- [ ] Coverage >= 95% (`pytest --cov=wdyaw`)
- [ ] `CHANGELOG.md` updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Version bumped in `wdyaw/__init__.py`
- [ ] Version bumped in `wdyaw/SKILL.md` frontmatter
- [ ] `SKILL.md` tested with at least one agent
- [ ] No sensitive data in repo

---

## Version Sync

Keep these files in sync when releasing:

| File | Field | Example |
|------|-------|---------|
| `pyproject.toml` | `project.version` | `version = "0.1.0"` |
| `wdyaw/__init__.py` | `__version__` | `__version__ = "0.1.0"` |
| `wdyaw/SKILL.md` | `metadata.version` | `version: "0.1.0"` |

---

## Troubleshooting

### Skill not discovered

- Verify directory name matches `name` in `SKILL.md`
- Check `SKILL.md` is all uppercase
- Validate frontmatter YAML syntax
- Ensure `description` is not empty

### PyPI upload fails

- Check `PYPI_API_TOKEN` secret is set
- Ensure version is not already published (PyPI is immutable)
- Verify `pyproject.toml` has valid metadata

### Tests fail on CI

- Check Python version compatibility (3.9+)
- Ensure all dependencies in `pyproject.toml`
- Verify no hardcoded paths in tests
