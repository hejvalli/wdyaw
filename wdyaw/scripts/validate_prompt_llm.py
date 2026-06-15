"""Probabilistic prompt validation using LLM-based semantic analysis.

Catches semantic edge cases that deterministic regex misses:
- Semantic negation: "Refrain from using complex terms"
- Implied negatives: "Keep it simple" (implies "don't be complex")
- Contextual hedge words: "Use relatively simple language"

When no LLM function is provided, falls back to built-in semantic
pattern matching using enhanced regex and heuristics.

Usage:
    from wdyaw.scripts.validate_prompt_llm import validate_llm
    report = validate_llm("Your prompt text here...")
"""

from __future__ import annotations

import json
import re


# ---------------------------------------------------------------------------
# Semantic negation patterns (deterministic regex misses these)
# ---------------------------------------------------------------------------

SEMANTIC_NEGATION_PATTERNS = [
    re.compile(r"\brefrain\s+from\b", re.IGNORECASE),
    re.compile(r"\bstay\s+away\s+from\b", re.IGNORECASE),
    re.compile(r"\bsteer\s+clear\s+of\b", re.IGNORECASE),
    re.compile(r"\bhold\s+back\s+from\b", re.IGNORECASE),
    re.compile(r"\bresist\s+(?:the\s+)?temptation\s+to\b", re.IGNORECASE),
    re.compile(r"\bshy\s+away\s+from\b", re.IGNORECASE),
    re.compile(r"\beschew\b", re.IGNORECASE),
    re.compile(r"\babstain\s+from\b", re.IGNORECASE),
    re.compile(r"\bforgo\b", re.IGNORECASE),
    re.compile(r"\bdo\s+without\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Implied negative patterns (positive phrasing that implies negation)
# ---------------------------------------------------------------------------

IMPLIED_NEGATIVE_PATTERNS = [
    re.compile(r"\bkeep\s+it\s+simple\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+it\s+brief\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+it\s+short\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+it\s+concise\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+it\s+straightforward\b", re.IGNORECASE),
    re.compile(r"\buse\s+simple\s+language\b", re.IGNORECASE),
    re.compile(r"\buse\s+plain\s+english\b", re.IGNORECASE),
    re.compile(r"\buse\s+accessible\s+language\b", re.IGNORECASE),
    re.compile(r"\bmaintain\s+clarity\b", re.IGNORECASE),
    re.compile(r"\bstick\s+to\s+the\s+point\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Contextual hedge patterns (hedges in context deterministic might miss)
# ---------------------------------------------------------------------------

CONTEXTUAL_HEDGE_PATTERNS = [
    re.compile(r"\buse\s+relatively\s+\w+\b", re.IGNORECASE),
    re.compile(r"\bkeep\s+it\s+fairly\s+\w+\b", re.IGNORECASE),
    re.compile(r"\bmake\s+it\s+quite\s+\w+\b", re.IGNORECASE),
    re.compile(r"\btry\s+to\s+be\s+more\s+or\s+less\b", re.IGNORECASE),
    re.compile(r"\baim\s+for\s+a\s+reasonably\s+\w+\b", re.IGNORECASE),
    re.compile(r"\bto\s+some\s+extent\b", re.IGNORECASE),
    re.compile(r"\bin\s+general\b", re.IGNORECASE),
    re.compile(r"\bgenerally\s+speaking\b", re.IGNORECASE),
    re.compile(r"\bfor\s+the\s+most\s+part\b", re.IGNORECASE),
    re.compile(r"\bmore\s+or\s+less\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# LLM structured validation prompt
# ---------------------------------------------------------------------------

LLM_VALIDATION_PROMPT = """You are a prompt validation expert. Analyze the following prompt text for semantic issues that simple keyword matching might miss.

Prompt to analyze:
---
{prompt_text}
---

Check for these specific issues:

1. SEMANTIC_NEGATION: Phrases that express negation indirectly (e.g., "refrain from", "steer clear of", "eschew", "abstain from"). These activate forbidden concepts through ironic process theory just like direct negation.

2. IMPLIED_NEGATIVE: Positive phrasing that implies a negative constraint without stating it positively (e.g., "keep it simple" implies "don't be complex", "use plain English" implies "don't use technical language"). These are less harmful than direct negation but still create ambiguity.

3. CONTEXTUAL_HEDGE: Hedge words used in ways that create ambiguity about expectations (e.g., "use relatively simple language", "make it quite clear", "aim for a reasonably brief response"). The hedge word + expectation combo creates a broad probability distribution.

For each finding, provide:
- category: "semantic_negation", "implied_negative", or "contextual_hedge"
- severity: "error" (semantic_negation), "warning" (implied_negative, contextual_hedge)
- text: the exact phrase found
- position: approximate character position (0-indexed)
- suggestion: how to reframe positively

Return ONLY valid JSON in this exact format:
{{
  "findings": [
    {{
      "category": "semantic_negation",
      "severity": "error",
      "text": "refrain from using",
      "position": 12,
      "suggestion": "Use straightforward language instead of technical terms"
    }}
  ],
  "semantic_negation_count": 1,
  "implied_negative_count": 0,
  "contextual_hedge_count": 0
}}

If no issues are found, return:
{{
  "findings": [],
  "semantic_negation_count": 0,
  "implied_negative_count": 0,
  "contextual_hedge_count": 0
}}
"""


def _find_semantic_matches(prompt_text: str) -> list[dict]:
    """Find semantic negation matches with context."""
    found = []
    text_lower = prompt_text.lower()

    for pattern in SEMANTIC_NEGATION_PATTERNS:
        for match in pattern.finditer(text_lower):
            start = max(0, match.start() - 20)
            end = min(len(prompt_text), match.end() + 20)
            context = prompt_text[start:end].replace("\n", " ")
            found.append({
                "word": prompt_text[match.start():match.end()],
                "context": f"...{context}...",
                "position": match.start(),
                "severity": "error",
                "category": "semantic_negation",
            })

    for pattern in IMPLIED_NEGATIVE_PATTERNS:
        for match in pattern.finditer(text_lower):
            start = max(0, match.start() - 20)
            end = min(len(prompt_text), match.end() + 20)
            context = prompt_text[start:end].replace("\n", " ")
            found.append({
                "word": prompt_text[match.start():match.end()],
                "context": f"...{context}...",
                "position": match.start(),
                "severity": "warning",
                "category": "implied_negative",
            })

    for pattern in CONTEXTUAL_HEDGE_PATTERNS:
        for match in pattern.finditer(text_lower):
            start = max(0, match.start() - 20)
            end = min(len(prompt_text), match.end() + 20)
            context = prompt_text[start:end].replace("\n", " ")
            found.append({
                "word": prompt_text[match.start():match.end()],
                "context": f"...{context}...",
                "position": match.start(),
                "severity": "warning",
                "category": "contextual_hedge",
            })

    seen_positions = set()
    unique_found = []
    for item in found:
        if item["position"] not in seen_positions:
            seen_positions.add(item["position"])
            unique_found.append(item)

    unique_found.sort(key=lambda x: x["position"])
    return unique_found


def _run_builtin_probabilistic(prompt_text: str) -> dict:
    """Run built-in probabilistic checks using semantic patterns."""
    matches = _find_semantic_matches(prompt_text)

    semantic_negation_matches = [m for m in matches if m["category"] == "semantic_negation"]
    implied_negative_matches = [m for m in matches if m["category"] == "implied_negative"]
    contextual_hedge_matches = [m for m in matches if m["category"] == "contextual_hedge"]

    checks = []

    checks.append({
        "name": "P04 — Semantic Negation (Indirect Negatives)",
        "passed": len(semantic_negation_matches) == 0,
        "details": {
            "count": len(semantic_negation_matches),
            "matches": semantic_negation_matches,
            "explanation": (
                "Semantic negations ('refrain from', 'steer clear of') activate "
                "forbidden concepts through ironic process theory, just like "
                "direct negation. Reframe as positive behavioral statements."
            ),
        },
    })

    checks.append({
        "name": "P05 — Implied Negative Constraints",
        "passed": len(implied_negative_matches) == 0,
        "details": {
            "count": len(implied_negative_matches),
            "matches": implied_negative_matches,
            "explanation": (
                "Implied negatives ('keep it simple') create ambiguity about "
                "what to avoid rather than what to do. Replace with explicit "
                "positive specifications."
            ),
        },
    })

    checks.append({
        "name": "P06 — Contextual Hedge Words",
        "passed": len(contextual_hedge_matches) == 0,
        "details": {
            "count": len(contextual_hedge_matches),
            "matches": contextual_hedge_matches,
            "explanation": (
                "Contextual hedges ('use relatively simple language') create "
                "broad probability distributions over outputs. Replace with "
                "specific thresholds or ranges."
            ),
        },
    })

    weights = {"P04": 30, "P05": 35, "P06": 35}
    total_score = 0
    for check in checks:
        check_id = check["name"][:3]
        weight = weights.get(check_id, 33)
        if check["passed"]:
            total_score += weight

    score = min(100, max(0, total_score))
    passed = score >= 50

    return {
        "passed": passed,
        "checks": checks,
        "score": score,
    }


def _run_llm_probabilistic(prompt_text: str, llm_fn: callable) -> dict:
    """Run probabilistic validation using an injected LLM function."""
    structured_prompt = LLM_VALIDATION_PROMPT.format(prompt_text=prompt_text)

    try:
        response = llm_fn(structured_prompt)
        if not response or not isinstance(response, str):
            return _run_builtin_probabilistic(prompt_text)

        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines).strip()

        data = json.loads(response)
        findings = data.get("findings", [])

        semantic_negation_matches = [
            {
                "word": f.get("text", ""),
                "context": f"...{f.get('text', '')}...",
                "position": f.get("position", 0),
                "severity": f.get("severity", "error"),
                "category": f.get("category", "semantic_negation"),
                "suggestion": f.get("suggestion", ""),
            }
            for f in findings
            if f.get("category") == "semantic_negation"
        ]

        implied_negative_matches = [
            {
                "word": f.get("text", ""),
                "context": f"...{f.get('text', '')}...",
                "position": f.get("position", 0),
                "severity": f.get("severity", "warning"),
                "category": f.get("category", "implied_negative"),
                "suggestion": f.get("suggestion", ""),
            }
            for f in findings
            if f.get("category") == "implied_negative"
        ]

        contextual_hedge_matches = [
            {
                "word": f.get("text", ""),
                "context": f"...{f.get('text', '')}...",
                "position": f.get("position", 0),
                "severity": f.get("severity", "warning"),
                "category": f.get("category", "contextual_hedge"),
                "suggestion": f.get("suggestion", ""),
            }
            for f in findings
            if f.get("category") == "contextual_hedge"
        ]

        checks = [
            {
                "name": "P04 — Semantic Negation (Indirect Negatives)",
                "passed": len(semantic_negation_matches) == 0,
                "details": {
                    "count": len(semantic_negation_matches),
                    "matches": semantic_negation_matches,
                    "explanation": (
                        "Semantic negations ('refrain from', 'steer clear of') "
                        "activate forbidden concepts through ironic process "
                        "theory, just like direct negation. Reframe as positive "
                        "behavioral statements."
                    ),
                },
            },
            {
                "name": "P05 — Implied Negative Constraints",
                "passed": len(implied_negative_matches) == 0,
                "details": {
                    "count": len(implied_negative_matches),
                    "matches": implied_negative_matches,
                    "explanation": (
                        "Implied negatives ('keep it simple') create ambiguity "
                        "about what to avoid rather than what to do. Replace "
                        "with explicit positive specifications."
                    ),
                },
            },
            {
                "name": "P06 — Contextual Hedge Words",
                "passed": len(contextual_hedge_matches) == 0,
                "details": {
                    "count": len(contextual_hedge_matches),
                    "matches": contextual_hedge_matches,
                    "explanation": (
                        "Contextual hedges ('use relatively simple language') "
                        "create broad probability distributions over outputs. "
                        "Replace with specific thresholds or ranges."
                    ),
                },
            },
        ]

        weights = {"P04": 30, "P05": 35, "P06": 35}
        total_score = sum(
            weights.get(check["name"][:3], 33)
            for check in checks
            if check["passed"]
        )
        score = min(100, max(0, total_score))
        passed = score >= 50

        return {
            "passed": passed,
            "checks": checks,
            "score": score,
        }

    except (json.JSONDecodeError, TypeError, ValueError):
        return _run_builtin_probabilistic(prompt_text)


def validate_llm(prompt_text: str, llm_fn: callable | None = None) -> dict:
    """Validate a prompt using probabilistic (LLM-based) analysis.

    Catches semantic edge cases that deterministic regex misses:
    - Semantic negation: "Refrain from using complex terms"
    - Implied negatives: "Keep it simple" (implies "don't be complex")
    - Contextual hedge words: "Use relatively simple language"

    When llm_fn is provided, uses the LLM for deeper semantic analysis.
    Otherwise falls back to built-in semantic pattern matching.

    Non-blocking by default. Only blocks when score < 50.

    Args:
        prompt_text: The prompt string to validate.
        llm_fn: Optional callable that takes a prompt string and returns
            an LLM response string. If None, uses built-in patterns.

    Returns:
        A structured validation report matching deterministic format:
        {
            "passed": bool,       # True if score >= 50
            "checks": [           # Per-check results (P04-P06)
                {
                    "name": str,
                    "passed": bool,
                    "details": dict,
                }
            ],
            "score": int,         # 0-100 overall quality score
        }

    Example:
        >>> result = validate_llm("Refrain from using jargon.")
        >>> result["checks"][0]["name"]
        'P04 — Semantic Negation (Indirect Negatives)'
    """
    if not isinstance(prompt_text, str):
        raise TypeError(f"prompt_text must be str, got {type(prompt_text).__name__}")

    if llm_fn is not None and callable(llm_fn):
        return _run_llm_probabilistic(prompt_text, llm_fn)

    return _run_builtin_probabilistic(prompt_text)


def main():
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Validate prompt using probabilistic analysis"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt text (reads from stdin if omitted)")
    args = parser.parse_args()

    prompt = args.prompt if args.prompt else sys.stdin.read()
    report = validate_llm(prompt)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
