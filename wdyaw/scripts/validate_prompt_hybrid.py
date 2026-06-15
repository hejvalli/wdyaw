"""Hybrid prompt validation orchestrator.

Combines deterministic + probabilistic validation with confidence-based routing:
- fast: deterministic only (default, <1ms)
- standard: deterministic + probabilistic for edge cases
- strict: deterministic + probabilistic, blocks on any issue

Usage:
    from wdyaw.scripts.validate_prompt_hybrid import validate_hybrid
    report = validate_hybrid("Your prompt text here...", mode="standard")
"""

from __future__ import annotations

from wdyaw.scripts.validate_prompt import validate
from wdyaw.scripts.validate_prompt_llm import validate_llm


MODE_FAST = "fast"
MODE_STANDARD = "standard"
MODE_STRICT = "strict"
VALID_MODES = {MODE_FAST, MODE_STANDARD, MODE_STRICT}


def _deduplicate_findings(det_checks: list[dict], prob_checks: list[dict]) -> list[dict]:
    """Merge and deduplicate findings from both validation layers.

    Removes exact duplicate matches (same position and word) while preserving
    unique findings from each layer.
    """
    merged = []
    seen = set()

    for check in det_checks:
        merged_check = {
            "name": check["name"],
            "passed": check["passed"],
            "layer": "deterministic",
            "details": {**check["details"]},
        }

        matches = check["details"].get("matches", [])
        deduped_matches = []
        for match in matches:
            key = (match.get("position", -1), match.get("word", "").lower())
            if key not in seen:
                seen.add(key)
                deduped_matches.append(match)

        merged_check["details"]["matches"] = deduped_matches
        merged_check["details"]["count"] = len(deduped_matches)
        merged.append(merged_check)

    for check in prob_checks:
        merged_check = {
            "name": check["name"],
            "passed": check["passed"],
            "layer": "probabilistic",
            "details": {**check["details"]},
        }

        matches = check["details"].get("matches", [])
        deduped_matches = []
        for match in matches:
            key = (match.get("position", -1), match.get("word", "").lower())
            if key not in seen:
                seen.add(key)
                deduped_matches.append(match)

        merged_check["details"]["matches"] = deduped_matches
        merged_check["details"]["count"] = len(deduped_matches)
        merged.append(merged_check)

    return merged


def _calculate_hybrid_score(merged_checks: list[dict]) -> int:
    """Calculate hybrid score from merged deterministic + probabilistic checks.

    Deterministic checks (P01-P03): 60% weight
    Probabilistic checks (P04-P06): 40% weight
    """
    det_checks = [c for c in merged_checks if c.get("layer") == "deterministic"]
    prob_checks = [c for c in merged_checks if c.get("layer") == "probabilistic"]

    det_score = 0
    prob_score = 0

    weights_det = {"P01": 24, "P02": 21, "P03": 15}
    weights_prob = {"P04": 12, "P05": 14, "P06": 14}

    for check in det_checks:
        check_id = check["name"][:3]
        weight = weights_det.get(check_id, 20)
        if check["passed"]:
            det_score += weight

    for check in prob_checks:
        check_id = check["name"][:3]
        weight = weights_prob.get(check_id, 13)
        if check["passed"]:
            prob_score += weight

    total = det_score + prob_score
    return min(100, max(0, total))


def _count_deduplicated(merged_checks: list[dict]) -> int:
    """Count total deduplicated findings across all checks."""
    total = 0
    for check in merged_checks:
        total += check["details"].get("count", 0)
    return total


def validate_hybrid(
    prompt_text: str,
    mode: str = MODE_FAST,
    llm_fn: callable | None = None,
) -> dict:
    """Validate a prompt using hybrid deterministic + probabilistic analysis.

    Confidence-based routing:
    - fast: deterministic only (default, <1ms). Non-blocking (score >= 50).
    - standard: deterministic + probabilistic. Non-blocking (score >= 50).
    - strict: deterministic + probabilistic. Blocks on any issue.

    The probabilistic layer catches semantic edge cases that deterministic
    regex misses (semantic negation, implied negatives, contextual hedges).

    Args:
        prompt_text: The prompt string to validate.
        mode: Validation mode — "fast", "standard", or "strict".
        llm_fn: Optional callable for LLM-based probabilistic validation.
            If None, uses built-in semantic patterns.

    Returns:
        A unified validation report:
        {
            "passed": bool,
            "mode": str,
            "checks": [             # Merged findings from both layers
                {
                    "name": str,
                    "passed": bool,
                    "layer": str,    # "deterministic" or "probabilistic"
                    "details": dict,
                }
            ],
            "score": int,
            "deterministic": dict,  # Raw deterministic report
            "probabilistic": dict,  # Raw probabilistic report (if run)
            "deduplicated_count": int,
        }

    Example:
        >>> result = validate_hybrid("Write a JSON summary.", mode="fast")
        >>> result["passed"]
        True
        >>> result = validate_hybrid("Don't be bad.", mode="strict")
        >>> result["passed"]
        False
    """
    if not isinstance(prompt_text, str):
        raise TypeError(f"prompt_text must be str, got {type(prompt_text).__name__}")

    if mode not in VALID_MODES:
        raise ValueError(
            f"mode must be one of {VALID_MODES}, got {mode!r}"
        )

    det_report = validate(prompt_text)

    if mode == MODE_FAST:
        return {
            "passed": det_report["passed"],
            "mode": mode,
            "checks": [
                {**check, "layer": "deterministic"}
                for check in det_report["checks"]
            ],
            "score": det_report["score"],
            "deterministic": det_report,
            "probabilistic": None,
            "deduplicated_count": 0,
        }

    prob_report = validate_llm(prompt_text, llm_fn)

    merged_checks = _deduplicate_findings(
        det_report["checks"], prob_report["checks"]
    )

    hybrid_score = _calculate_hybrid_score(merged_checks)

    if mode == MODE_STRICT:
        passed = all(check["passed"] for check in merged_checks)
    else:
        passed = hybrid_score >= 50

    return {
        "passed": passed,
        "mode": mode,
        "checks": merged_checks,
        "score": hybrid_score,
        "deterministic": det_report,
        "probabilistic": prob_report,
        "deduplicated_count": _count_deduplicated(merged_checks),
    }


def main():
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Hybrid prompt validation (deterministic + probabilistic)"
    )
    parser.add_argument("prompt", nargs="?", help="Prompt text (reads from stdin if omitted)")
    parser.add_argument(
        "--mode",
        choices=[MODE_FAST, MODE_STANDARD, MODE_STRICT],
        default=MODE_FAST,
        help="Validation mode (default: fast)",
    )
    args = parser.parse_args()

    prompt = args.prompt if args.prompt else sys.stdin.read()
    report = validate_hybrid(prompt, mode=args.mode)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
