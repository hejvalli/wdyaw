# Prompt Patterns Quick Reference

Concise patterns and templates for reliable LLM outputs.

---

## TCRTE Framework

| Component | Description | Example |
|-----------|-------------|---------|
| **T — Task** | What the AI should produce | "Summarize this article in 3 bullet points" |
| **C — Context** | Audience, purpose, constraints | "Audience: busy executives. Tone: concise. Exclude jargon." |
| **R — References** | Style examples, format templates | "Use the format shown below. Follow AP style." |
| **T — Testing** | Success criteria | "Must be under 150 words. Must cover all 3 main points." |
| **E — Enhancement** | Iteration plan | "If word count is exceeded, compress while preserving key points." |

**Full TCRTE Prompt:**

```
Task: Write a product description under 100 words.
Context: Target audience is seniors (65+). Emphasize ease of use.
References: See attached example descriptions for tone.
Testing: Must include 3 benefits, 0 technical specs, and a CTA.
Enhancement: If too long, remove adjectives before cutting benefits.
```

---

## Format Templates

### XML Format

```xml
<instructions>Summarize the following in 2 bullet points.</instructions>
<context>Audience: executives with no technical background.</context>
<data>Artificial intelligence is transforming healthcare...</data>
```

### Markdown Format

```markdown
## Task
Summarize the following in 2 bullet points.

## Context
- Audience: executives with no technical background
- Tone: concise, professional

## Data
Artificial intelligence is transforming healthcare...
```

---

## Role Assignment Examples

| Role | Prompt |
|------|--------|
| **Expert** | "You are a senior software architect with 20 years of experience designing distributed systems." |
| **Editor** | "You are a meticulous copyeditor. Fix grammar, tighten prose, and flag unclear sentences." |
| **Skeptic** | "You are a critical security auditor. Find vulnerabilities and rate each by severity." |
| **Teacher** | "You are a patient tutor explaining concepts to a beginner. Use analogies and check for understanding." |

---

## Vague vs. Specific Prompts

### Example 1 — Marketing Content

**Vague:**
```
Write something about marketing.
```

**Specific:**
```
Write a 200-word LinkedIn post about social media strategy for B2B SaaS companies, focusing on LinkedIn. Include one actionable tip and end with a question to drive engagement.
```

### Example 2 — Editing Task

**Vague:**
```
Make this better.
```

**Specific:**
```
Rewrite this email to be more concise (under 100 words), maintain a professional but friendly tone, and include a clear call-to-action with a deadline of Friday.
```

### Example 3 — Technical Explanation

**Vague:**
```
Explain quantum computing.
```

**Specific:**
```
Explain quantum computing to a high school student in 3 short paragraphs. Use one analogy. Avoid mathematical formulas. Define "qubit" and "superposition" in plain language.
```

### Example 4 — Code Generation

**Vague:**
```
Write a function to process data.
```

**Specific:**
```
Write a Python function `filter_active_users(users: list[dict]) -> list[dict]` that returns users where `status == "active"` and `last_login` is within 30 days. Include type hints and a docstring.
```

---

## Quick Tips

- **Sandwich important instructions** — place the core request at both the beginning and end of the prompt
- **Use positive constraints** ("Use simple language") over negative ones ("Don't use jargon")
- **Show, don't tell** — provide concrete examples of desired output format
- **List constraints explicitly** as a bulleted block for 90%+ compliance vs. 70% when embedded in prose
- **Close all XML tags** — unclosed tags confuse section boundaries
- **Keep system prompts stable** (role, rules, format defaults) and user prompts dynamic (task, data, context)
