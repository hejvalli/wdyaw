"""Prompt validation script with P01-P03 failure pattern detection.

Validates prompt text against three validated failure patterns:
- P01 (Pink Elephant): Negative constraints activate forbidden concepts
- P02 (Vague Qualifiers): Hedge words reduce accuracy
- P03 (Format Ambiguity): Missing format specification degrades performance

Usage:
    from wdyaw.scripts.validate_prompt import validate
    report = validate("Your prompt text here...")
"""

import re


# ---------------------------------------------------------------------------
# Detection lexicons (deterministic, regex-based)
# ---------------------------------------------------------------------------

# P01 — Pink Elephant: negation tokens that precede content-bearing words.
# Detection confidence: HIGH (deterministic lexical match).
P01_NEGATION_PATTERNS = [
    re.compile(r"\bdon['\u2019]t\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    re.compile(r"\bavoid\b", re.IGNORECASE),
    re.compile(r"\bdo not\b", re.IGNORECASE),
    re.compile(r"\bprevent\b", re.IGNORECASE),
    re.compile(r"\bmust not\b", re.IGNORECASE),
    re.compile(r"\bshould not\b", re.IGNORECASE),
    re.compile(r"\bcannot\b", re.IGNORECASE),
    re.compile(r"\bcan't\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:jargon|fluff|bs|bullshit|assumptions)\b", re.IGNORECASE),
    re.compile(r"\b(?:strictly\s+)?prohibited\b", re.IGNORECASE),
    re.compile(r"\bbanned\b", re.IGNORECASE),
]

# P02 — Vague Qualifiers: hedge words that create broad probability distributions.
# Expanded from CoNLL-2010 shared task with prompt-specific qualifiers.
P02_HEDGE_PATTERNS = [
    re.compile(r"\bsomewhat\b", re.IGNORECASE),
    re.compile(r"\bmaybe\b", re.IGNORECASE),
    re.compile(r"\bperhaps\b", re.IGNORECASE),
    re.compile(r"\bpossibly\b", re.IGNORECASE),
    re.compile(r"\bif possible\b", re.IGNORECASE),
    re.compile(r"\bif you can\b", re.IGNORECASE),
    re.compile(r"\btry to\b", re.IGNORECASE),
    re.compile(r"\battempt to\b", re.IGNORECASE),
    re.compile(r"\brelatively\b", re.IGNORECASE),
    re.compile(r"\breasonably\b", re.IGNORECASE),
    re.compile(r"\bfairly\b", re.IGNORECASE),
    re.compile(r"\bquite\b", re.IGNORECASE),
    re.compile(r"\bmore or less\b", re.IGNORECASE),
    re.compile(r"\bkind of\b", re.IGNORECASE),
    re.compile(r"\bsort of\b", re.IGNORECASE),
    re.compile(r"\bish\b", re.IGNORECASE),
    re.compile(r"\broughly\b", re.IGNORECASE),
    re.compile(r"\bapproximately\b", re.IGNORECASE),
    re.compile(r"\baround\b", re.IGNORECASE),
    re.compile(r"\bgenerally\b", re.IGNORECASE),
    re.compile(r"\bwhen appropriate\b", re.IGNORECASE),
    re.compile(r"\bwhere applicable\b", re.IGNORECASE),
    re.compile(r"\bas needed\b", re.IGNORECASE),
    re.compile(r"\ba bit\b", re.IGNORECASE),
    re.compile(r"\bto some extent\b", re.IGNORECASE),
    re.compile(r"\bin general\b", re.IGNORECASE),
]

# P03 — Format Ambiguity: explicit format specifications prevent degradation.
P03_FORMAT_PATTERNS = [
    re.compile(r"\bjson\b", re.IGNORECASE),
    re.compile(r"\bxml\b", re.IGNORECASE),
    re.compile(r"\bmarkdown\b", re.IGNORECASE),
    re.compile(r"\bmd\b", re.IGNORECASE),
    re.compile(r"\bbullet points\b", re.IGNORECASE),
    re.compile(r"\bbulleted list\b", re.IGNORECASE),
    re.compile(r"\bbullet list\b", re.IGNORECASE),
    re.compile(r"\bnumbered list\b", re.IGNORECASE),
    re.compile(r"\bnumbered steps\b", re.IGNORECASE),
    re.compile(r"\bstep-by-step\b", re.IGNORECASE),
    re.compile(r"\btable\b", re.IGNORECASE),
    re.compile(r"\btabular\b", re.IGNORECASE),
    re.compile(r"\bcsv\b", re.IGNORECASE),
    re.compile(r"\btsv\b", re.IGNORECASE),
    re.compile(r"\bcode block\b", re.IGNORECASE),
    re.compile(r"\bcode snippet\b", re.IGNORECASE),
    re.compile(r"\bpseudocode\b", re.IGNORECASE),
    re.compile(r"\byaml\b", re.IGNORECASE),
    re.compile(r"\btoml\b", re.IGNORECASE),
    re.compile(r"\bini\b", re.IGNORECASE),
    re.compile(r"\bparagraph\b", re.IGNORECASE),
    re.compile(r"\bessay\b", re.IGNORECASE),
    re.compile(r"\breport\b", re.IGNORECASE),
    re.compile(r"\bsummary\b", re.IGNORECASE),
    re.compile(r"\bdiagram\b", re.IGNORECASE),
    re.compile(r"\bflowchart\b", re.IGNORECASE),
    re.compile(r"\bmermaid\b", re.IGNORECASE),
]


def _find_pattern_matches(
    prompt_text: str,
    patterns: list[re.Pattern],
) -> list[dict]:
    """Generic helper: find all pattern matches with context.

    Returns deduplicated, sorted list of match dicts.
    """
    found = []
    text_lower = prompt_text.lower()

    for pattern in patterns:
        for match in pattern.finditer(text_lower):
            start = max(0, match.start() - 20)
            end = min(len(prompt_text), match.end() + 20)
            context = prompt_text[start:end].replace("\n", " ")
            found.append({
                "word": prompt_text[match.start():match.end()],
                "context": f"...{context}...",
                "position": match.start(),
            })

    seen_positions = set()
    unique_found = []
    for item in found:
        if item["position"] not in seen_positions:
            seen_positions.add(item["position"])
            unique_found.append(item)

    unique_found.sort(key=lambda x: x["position"])
    return unique_found


# P01 severity classification patterns
P01_CRITICAL_PATTERNS = [
    re.compile(r"\bnever\b.*?\b(?:reveal|share|disclose|provide)\b.*?\b(?:personal\s+(?:information|info)|pii|medical\s+advice|legal\s+advice|financial\s+advice|confidential)\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\b.*?\b(?:provide|discuss|mention)\b.*?\b(?:medical|legal|financial)\b.*?\b(?:advice|claims)\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\b.*?\b(?:share|reveal|disclose)\b.*?\b(?:personal|confidential|private)\b.*?\b(?:data|information)\b", re.IGNORECASE),
    re.compile(r"\bnever\b.*?\b(?:fabricate|hallucinate)\b.*?\b(?:statistics|sources|data|information)\b", re.IGNORECASE),
    re.compile(r"\bmust\s+not\b.*?\b(?:share|reveal|disclose)\b", re.IGNORECASE),
    re.compile(r"\bstrictly\s+prohibited\b", re.IGNORECASE),
    re.compile(r"\bbanned\b.*?\b(?:words|phrases|terms)\b", re.IGNORECASE),
    re.compile(r"\bnever\b.*?\buse\b.*?\b(?:emojis|exclamation\s+marks)\b", re.IGNORECASE),
]

P01_WARNING_PATTERNS = [
    re.compile(r"\bavoid\b.*?\b(?:technical|jargon|verbose|fluff|casual)\b", re.IGNORECASE),
    re.compile(r"\b(?:never|do\s+not)\b.*?\binclude\b.*?\b(?:introduction|conclusion|markdown)\b", re.IGNORECASE),
    re.compile(r"\bdon['\u2019]t\b.*?\buse\b.*?\b(?:slang|ellipses)\b", re.IGNORECASE),
]

P01_ERROR_PATTERNS = [
    re.compile(r"\bdon['\u2019]t\b.*?\bbe\b.*?\b(?:bad|wrong|stupid|generic)\b", re.IGNORECASE),
    re.compile(r"\bnever\b.*?\bmake\b.*?\b(?:mistakes|errors)\b", re.IGNORECASE),
]


def _classify_p01_severity(match_word: str, match_context: str) -> str:
    """Classify a P01 match by severity based on the matched word and context.

    Analyzes the matched negation word and surrounding text to determine if
    the negative constraint is a safety/compliance hard stop (critical), a
    format/style preference with positive alternatives (warning), or a vague
    negative with no clear positive alternative (error).

    Args:
        match_word: The specific negation word that was matched.
        match_context: Surrounding text (±30 chars) of the match.

    Returns:
        "critical" — Safety/compliance/legal/privacy hard stops (allowed)
        "warning" — Format/structural constraints with clear alternatives
        "error" — Vague negatives with no clear positive alternative (fails)
    """
    text = match_context.lower().replace("\n", " ")
    word_lower = match_word.lower()

    # CRITICAL: Safety/compliance/legal/privacy hard stops
    for pattern in P01_CRITICAL_PATTERNS:
        match = pattern.search(text)
        if match:
            # Verify the critical pattern involves the matched negation word,
            # not a different negation word elsewhere in the context
            critical_start = match.start()
            # Check if the matched negation word is within the critical match
            if word_lower in text[critical_start : match.end()]:
                return "critical"

    # WARNING: Format/structural constraints, style preferences
    for pattern in P01_WARNING_PATTERNS:
        match = pattern.search(text)
        if match:
            warning_start = match.start()
            if word_lower in text[warning_start : match.end()]:
                return "warning"

    # ERROR: Vague negatives with no clear positive alternative
    for pattern in P01_ERROR_PATTERNS:
        match = pattern.search(text)
        if match:
            error_start = match.start()
            if word_lower in text[error_start : match.end()]:
                return "error"

    # Default: any negative not matching critical or warning
    return "error"


def _detect_p01(prompt_text: str) -> dict:
    """Detect P01 (Pink Elephant) negative constraints.

    Scans for negation words that activate forbidden concepts through
    ironic process theory. Returns all matches with context and severity.
    """
    unique_found = _find_pattern_matches(prompt_text, P01_NEGATION_PATTERNS)

    for match in unique_found:
        pos = match["position"]
        match_len = len(match["word"])
        start = max(0, pos - 30)
        end = min(len(prompt_text), pos + match_len + 30)
        classification_context = prompt_text[start:end].replace("\n", " ")
        match["severity"] = _classify_p01_severity(match["word"], classification_context)

    severity_counts = {"critical": 0, "warning": 0, "error": 0}
    for match in unique_found:
        severity_counts[match["severity"]] += 1

    has_errors = severity_counts["error"] > 0

    return {
        "name": "P01 — Pink Elephant (Negative Constraints)",
        "passed": not has_errors,
        "details": {
            "count": len(unique_found),
            "matches": unique_found,
            "severity_counts": severity_counts,
            "explanation": (
                "Negative constraints ('don't', 'never', 'avoid') activate "
                "forbidden concepts through ironic process theory. "
                "Reframe as positive behavioral statements."
            ),
        },
    }


def _detect_p02(prompt_text: str) -> dict:
    """Detect P02 (Vague Qualifiers) hedge words.

    Scans for hedging language that creates broad probability distributions
    over possible outputs, reducing accuracy by 22.6-93.1%.
    """
    unique_found = _find_pattern_matches(prompt_text, P02_HEDGE_PATTERNS)

    return {
        "name": "P02 — Vague Qualifiers (Hedge Words)",
        "passed": len(unique_found) == 0,
        "details": {
            "count": len(unique_found),
            "matches": unique_found,
            "explanation": (
                "Hedge words ('somewhat', 'maybe', 'if possible') reduce "
                "accuracy by 22.6-93.1%. Replace with specific ranges or thresholds."
            ),
        },
    }


def _detect_p03(prompt_text: str) -> dict:
    """Detect P03 (Format Ambiguity) missing format specification.

    Checks for explicit format keywords. Absence causes 28.76% performance
    degradation on average.
    """
    text_lower = prompt_text.lower()
    found_formats = []

    for pattern in P03_FORMAT_PATTERNS:
        match = pattern.search(text_lower)
        if match:
            found_formats.append(match.group(0))

    # Also check for structural examples (indicated by "example:" or "like:")
    has_structural_example = bool(
        re.search(r"\b(example|e\.g\.|for example|like this|as follows)\b", text_lower)
    )

    # Also check for schema definition indicators
    has_schema = bool(
        re.search(r"\b(schema|structure|fields|keys|columns|attributes)\b", text_lower)
    )

    passed = bool(found_formats or has_structural_example or has_schema)

    return {
        "name": "P03 — Format Ambiguity (Missing Format)",
        "passed": passed,
        "details": {
            "found_formats": found_formats,
            "has_structural_example": has_structural_example,
            "has_schema": has_schema,
            "explanation": (
                "Missing format specification causes 28.76% performance degradation. "
                "Specify output format (JSON, markdown, bullet points, etc.)."
            ),
        },
    }


def _calculate_score(checks: list[dict]) -> int:
    """Calculate overall validation score (0-100).

    Each passed check contributes points. P01 and P02 are weighted
    more heavily due to higher documented impact.

    P01 uses severity-weighted scoring:
    - Critical matches: 0 point deduction (allowed)
    - Warning matches: 10 point deduction per match (capped at weight)
    - Error matches: 40 point deduction (full weight)
    """
    if not checks:
        return 0

    # Weights based on documented impact severity
    weights = {
        "P01": 40,  # Pink Elephant — high impact, high confidence
        "P02": 35,  # Vague Qualifiers — up to 93.1% accuracy drop
        "P03": 25,  # Format Ambiguity — 28.76% degradation
    }

    total_score = 0
    for check in checks:
        check_id = check["name"][:3]  # "P01", "P02", "P03"
        weight = weights.get(check_id, 33)

        if check_id == "P01":
            severity_counts = check["details"].get("severity_counts", {})
            if not severity_counts and not check["passed"]:
                # Backward compatibility: old checks without severity_counts
                # treated as having errors (full deduction)
                check_score = 0
            else:
                warning_count = severity_counts.get("warning", 0)
                error_count = severity_counts.get("error", 0)
                deduction = (warning_count * 10) + (error_count * 40)
                check_score = max(0, weight - deduction)
            total_score += check_score
        else:
            if check["passed"]:
                total_score += weight

    return min(100, max(0, total_score))


def validate(prompt_text: str) -> dict:
    """Validate a prompt against P01-P03 failure patterns.

    Performs deterministic lexical scanning to detect:
    - P01 (Pink Elephant): Negative constraints like "don't", "never", "avoid"
    - P02 (Vague Qualifiers): Hedge words like "somewhat", "maybe", "if possible"
    - P03 (Format Ambiguity): Missing format specification

    Non-blocking by default. Returns full report with recommendations.
    Only blocks when score < 50 (catastrophic failure).

    Args:
        prompt_text: The prompt string to validate.

    Returns:
        A structured validation report:
        {
            "passed": bool,       # True if score >= 50 (non-blocking)
            "checks": [           # Per-check results
                {
                    "name": str,
                    "passed": bool,
                    "details": dict,
                }
            ],
            "score": int,         # 0-100 overall quality score
        }

    Example:
        >>> result = validate("Don't be verbose. Write about cats.")
        >>> result["passed"]
        True
        >>> result["checks"][0]["name"]
        'P01 — Pink Elephant (Negative Constraints)'
    """
    if not isinstance(prompt_text, str):
        raise TypeError(f"prompt_text must be str, got {type(prompt_text).__name__}")

    # Run all three detection checks
    checks = [
        _detect_p01(prompt_text),
        _detect_p02(prompt_text),
        _detect_p03(prompt_text),
    ]

    # Calculate quality score
    score = _calculate_score(checks)

    # Non-blocking: only block on catastrophic failure (score < 50)
    passed = score >= 50

    return {
        "passed": passed,
        "checks": checks,
        "score": score,
    }


def main():
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Validate prompt against P01-P03 failure patterns")
    parser.add_argument("prompt", nargs="?", help="Prompt text (reads from stdin if omitted)")
    args = parser.parse_args()

    prompt = args.prompt if args.prompt else sys.stdin.read()
    report = validate(prompt)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
