# WDYAW — What Do You Actually Want

[![CI](https://github.com/hejvalli/WDYAW/actions/workflows/ci.yml/badge.svg)](https://github.com/hejvalli/WDYAW/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A conversational prompt architect that interviews users to capture true intent and generates production-ready prompts using the **TCRTE framework**.

**Warm but direct. No filler. No hedging.**

## What It Does

WDYAW solves the "vague prompt" problem. Instead of guessing what the user wants, it conducts a structured interview to extract:

- **T**ask — What action should the AI perform?
- **C**ontext — Who is the audience? What are the constraints?
- **R**eferences — Examples, templates, success criteria
- **T**esting — How will you know it worked?
- **E**nhancement — Tone, iteration strategy, preferences

Then it assembles a production-ready prompt with automatic validation against three proven failure patterns (P01-P03).

## Quick Start

WDYAW is an agent skill. Install it into your AI coding agent and it activates automatically when you express vague prompt intent.

### Install

WDYAW is an agent skill compatible with OpenCode, Claude Code, Cursor, and any agent supporting the Agent Skills specification.

#### Install

If `npx skills` is available, you can install directly from GitHub:

```bash
# Install to current project
npx skills add hejvalli/WDYAW

# Install globally (available everywhere)
npx skills add hejvalli/WDYAW --global

# Target specific agent
npx skills add hejvalli/WDYAW --agent claude-code
npx skills add hejvalli/WDYAW --agent opencode
```

**Use it:**

```bash
# In Claude Code or OpenCode
/skill wdyaw

# Or just express vague intent and it auto-activates:
"help me write a prompt about cats"
```

#### Manual install

If `npx skills` is unavailable, copy the skill directory manually:

```bash
# Clone the repo
git clone https://github.com/hejvalli/WDYAW.git

# For OpenCode (project-level)
cp -r WDYAW/wdyaw .opencode/skills/

# For OpenCode (global)
cp -r WDYAW/wdyaw ~/.config/opencode/skills/

# For Claude Code
cp -r WDYAW/wdyaw ~/.claude/skills/

# For OpenAI Codex
cp -r WDYAW/wdyaw ~/.codex/skills/

# For Cursor
cp -r WDYAW/wdyaw .cursor/skills/
```

## The TCRTE Framework

WDYAW uses a structured interview protocol to extract intent:

1. **Opening** (turns 1-2): One open-ended question. "Tell me what you're trying to accomplish."
2. **Exploration** (turns 3-5): Targeted slot-filling. One question per turn for missing TCRTE components.
3. **Confirmation** (turns 6-7): Summarize gathered components. Generate prompt when user confirms.

**Stop conditions**: Coverage >= 80% of TCRTE components, OR turns >= 7, OR user signals sufficient information.

## P01-P03 Failure Pattern Detection

Before delivering any prompt, WDYAW validates against three documented failure patterns:

| Pattern | Name | Impact | Detection |
|---------|------|--------|-----------|
| **P01** | Pink Elephant (Negative Constraints) | Activates forbidden concepts via ironic process theory | Detects: "don't", "never", "avoid", "do not" |
| **P02** | Vague Qualifiers (Hedge Words) | Reduces accuracy by 22.6-93.1% | Detects: "somewhat", "maybe", "if possible", "try to" |
| **P03** | Format Ambiguity (Missing Format) | Causes 28.76% performance degradation | Detects absence of: JSON, markdown, bullet points, tables, etc. |

All detection is **deterministic** (regex-based, no LLM calls) and runs in <1ms.

## Deterministic Scripts

The package includes three tested, deterministic scripts:

- **`sanitize_input.py`** — Detects injection attempts, strips zero-width characters, normalizes Unicode (NFKC), scores risk. Raises `SanitizationError` if blocked.
- **`validate_prompt.py`** — Scans prompt text against P01-P03 patterns. Returns structured report with score 0-100.
- **`assemble_prompt.py`** — Assembles TCRTE components into Markdown or XML format. Applies positive reframing automatically ("don't be verbose" → "keep responses under 150 words").

## Project Structure

```
WDYAW/
├── wdyaw/                      # Skill directory
│   ├── SKILL.md                # Agent skill definition
│   ├── scripts/                # Deterministic validation scripts
│   │   ├── sanitize_input.py
│   │   ├── validate_prompt.py
│   │   └── assemble_prompt.py
│   └── references/
│       └── prompt-patterns.md  # P01-P03 reference documentation
├── tests/                      # Test suite (167 tests, 99% coverage)
├── README.md                   # This file
└── LICENSE                     # MIT
```

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Publishing

See [PUBLISHING.md](PUBLISHING.md) for platform-specific release instructions (skills.sh, OpenCode, etc.).
