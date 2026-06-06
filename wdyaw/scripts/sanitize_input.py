import re
import unicodedata


class SanitizationError(ValueError):
    """Raised when input fails sanitization checks.

    Carries metadata for inspection by callers.
    """

    def __init__(self, message: str, metadata: dict):
        super().__init__(message)
        self.metadata = metadata


INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r'\bignore\s+(all\s+)?(previous|prior)\s+instructions?\b', re.IGNORECASE),
    re.compile(r'\bdisregard\s+(all\s+)?(previous|prior)\s+', re.IGNORECASE),
    re.compile(r'(?:^|\n)\s*system\s*:', re.IGNORECASE),
    re.compile(r'\b(?:enable|enter|activate|turn\s+on)\s+developer\s+mode\b', re.IGNORECASE),
    re.compile(r'\bforget\s+(everything\s+)?(you\s+)?(were\s+)?told\b', re.IGNORECASE),
]

HIGH_RISK_KEYWORDS: list[str] = [
    'ignore',
    'override',
    'bypass',
    'jailbreak',
    'secret',
    'hidden instructions',
]

MIN_INPUT_LENGTH: int = 5
MAX_INPUT_LENGTH: int = 2000
RISK_THRESHOLD: float = 0.5

_ZERO_WIDTH_CHARS: str = '\u200b\u200c\u200d\ufeff\u2060\u2061\u2062\u2063'


def _strip_zero_width(text: str) -> str:
    return text.translate(str.maketrans('', '', _ZERO_WIDTH_CHARS))


def sanitize(
    user_input: str,
    min_length: int = MIN_INPUT_LENGTH,
    max_length: int = MAX_INPUT_LENGTH,
    risk_threshold: float = RISK_THRESHOLD,
) -> tuple[str, dict]:
    metadata = {
        'original_length': len(user_input),
        'patterns_found': [],
        'was_modified': False,
        'risk_score': 0.0,
        'blocked': False,
    }

    if not (min_length <= len(user_input) <= max_length):
        metadata['blocked'] = True
        raise SanitizationError(
            "Input length out of allowed bounds",
            metadata,
        )

    cleaned = unicodedata.normalize('NFKC', user_input)
    cleaned = _strip_zero_width(cleaned)

    for pattern in INJECTION_PATTERNS:
        if pattern.search(cleaned):
            metadata['patterns_found'].append(pattern.pattern)
            metadata['risk_score'] += 0.3
            metadata['blocked'] = True
            raise SanitizationError(
                "Input blocked: injection pattern detected",
                metadata,
            )

    cleaned_lower = cleaned.lower()
    for keyword in HIGH_RISK_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", cleaned_lower, re.IGNORECASE):
            metadata['risk_score'] += 0.1

    metadata['risk_score'] = min(metadata['risk_score'], 1.0)

    if metadata['risk_score'] >= risk_threshold:
        metadata['blocked'] = True
        raise SanitizationError(
            "Risk score exceeds allowed threshold",
            metadata,
        )

    cleaned = cleaned.strip()
    metadata['was_modified'] = cleaned != user_input

    return cleaned, metadata


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Sanitize user input for prompt processing")
    parser.add_argument("input", nargs="?", help="Input text (reads from stdin if omitted)")
    parser.add_argument("--max-length", type=int, default=MAX_INPUT_LENGTH, help="Maximum input length")
    parser.add_argument("--risk-threshold", type=float, default=RISK_THRESHOLD, help="Risk score threshold")
    args = parser.parse_args()

    text = args.input if args.input else sys.stdin.read()

    try:
        result_text, result_meta = sanitize(text, max_length=args.max_length, risk_threshold=args.risk_threshold)
        print(f"SANITIZED: {result_text}")
        print(f"METADATA: {result_meta}")
    except SanitizationError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
