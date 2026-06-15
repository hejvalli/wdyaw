"""TCRTE Prompt Assembly Script.

Assembles prompt components into production-ready prompts using the TCRTE framework:
Context → Task → References → Testing → Enhancement.

Supports Markdown (simple prompts) and XML (complex multi-section prompts) output formats.
Applies positive reframing to convert negative constraints into positive specifications.

Adaptive mode (opt-in) detects implicit signals in component text and selects
optimal component ordering, resolves overlaps, and applies domain-aware reframing.

Usage:
    from wdyaw.scripts.assemble_prompt import assemble
    prompt = assemble(components, format_type="markdown")
    prompt = assemble(components, format_type="markdown", adaptive=True)
"""

import re
import xml.sax.saxutils as xmlutils
from typing import Any, Optional


# Positive reframing rules: negative constraint -> positive specification
# Order matters: more specific patterns should come before general ones.
REFRAME_RULES = [
    (
        r"\bdon['\u2019]?t\s+be\s+verbose\b",
        "keep responses under 150 words. Prioritize conciseness.",
    ),
    (
        r"\bdon['\u2019]?t\s+use\s+jargon\b",
        "use simple, everyday language accessible to non-experts.",
    ),
    (
        r"\bdon['\u2019]?t\s+include\s+fluff\b",
        "start directly with the core argument. Every sentence must add information.",
    ),
    (
        r"\bdon['\u2019]?t\s+make\s+assumptions\b",
        "ask for clarification when any requirement is ambiguous.",
    ),
    (
        r"\bavoid\s+technical\s+terms\b",
        "use language accessible to non-experts.",
    ),
    (
        r"\bnever\s+be\s+verbose\b",
        "keep responses under 150 words. Prioritize conciseness.",
    ),
    (
        r"\bnever\s+use\s+jargon\b",
        "use simple, everyday language accessible to non-experts.",
    ),
]

ADAPTIVE_REFRAME_RULES = [
    (r"\brefrain\s+from\s+using\b", "use alternative approaches instead."),
    (r"\bsteer\s+clear\s+of\b", "focus on different aspects."),
    (r"\bavoid\s+using\b", "use alternative approaches instead."),
    (r"\bskip\s+the\b", "proceed directly without the"),
    (r"\bomit\b", "exclude"),
    (r"\bleave\s+out\b", "exclude"),
    (r"\brefrain\s+from\b", "avoid"),
    (r"\bdo\s+without\b", "exclude"),
    (r"\bdon['\u2019]?t\s+be\s+repetitive\b", "ensure each sentence adds new information."),
    (r"\bdon['\u2019]?t\s+oversimplify\b", "maintain appropriate depth and nuance."),
    (r"\bdon['\u2019]?t\s+overcomplicate\b", "present ideas clearly and directly."),
    (r"\bnever\s+repeat\s+yourself\b", "ensure each sentence adds new information."),
]


_CRITICAL_CONSTRAINT_PATTERNS = [
    r"\bnever\b.*\b(?:share|reveal|disclose|provide)\b.*\b(?:personal|pii|confidential|private|medical|legal|financial)\b",
    r"\bdo\s+not\b.*\b(?:provide|discuss|mention)\b.*\b(?:medical|legal|financial)\b.*\b(?:advice|claims)\b",
    r"\bdo\s+not\b.*\b(?:share|reveal|disclose)\b.*\b(?:personal|confidential|private)\b.*\b(?:data|information)\b",
    r"\bnever\b.*\b(?:fabricate|hallucinate)\b.*\b(?:statistics|sources|data)\b",
    r"\bmust\s+not\b.*\b(?:share|reveal|disclose)\b",
    r"\bstrictly\s+prohibited\b",
    r"\bbanned\b.*\b(?:phrases|words|terms)\b",
    r"\bnever\b.*\buse\b.*\bemojis\b",
]


FORMAT_KEYWORDS = {
    "json": "json",
    "xml": "xml",
    "markdown": "markdown",
    "md": "markdown",
    "bullet points": "bullet points",
    "bulleted list": "bullet points",
    "bullet list": "bullet points",
    "numbered list": "numbered list",
    "numbered steps": "numbered steps",
    "step-by-step": "step-by-step",
    "table": "table",
    "tabular": "table",
    "csv": "csv",
    "tsv": "tsv",
    "code block": "code block",
    "code snippet": "code block",
    "pseudocode": "pseudocode",
    "yaml": "yaml",
    "toml": "toml",
    "ini": "ini",
    "paragraph": "paragraph",
    "essay": "essay",
    "report": "report",
    "summary": "summary",
    "diagram": "diagram",
    "flowchart": "flowchart",
    "mermaid": "mermaid",
}

AUDIENCE_PATTERNS = [
    re.compile(r"\bfor\s+(?:seniors|beginners|experts|children|kids|students|professionals|executives|developers|engineers|non-technical|technical)\b", re.IGNORECASE),
    re.compile(r"\btarget\s+(?:audience|reader|user)\b", re.IGNORECASE),
    re.compile(r"\baudience[:\s]", re.IGNORECASE),
    re.compile(r"\breader[:\s]", re.IGNORECASE),
]

TONE_PATTERNS = [
    (re.compile(r"\bprofessional\b", re.IGNORECASE), "professional"),
    (re.compile(r"\bcasual\b", re.IGNORECASE), "casual"),
    (re.compile(r"\bfriendly\b", re.IGNORECASE), "friendly"),
    (re.compile(r"\bformal\b", re.IGNORECASE), "formal"),
    (re.compile(r"\benthusiastic\b", re.IGNORECASE), "enthusiastic"),
    (re.compile(r"\bserious\b", re.IGNORECASE), "serious"),
    (re.compile(r"\bhumorous\b", re.IGNORECASE), "humorous"),
    (re.compile(r"\bsarcastic\b", re.IGNORECASE), "sarcastic"),
    (re.compile(r"\bempathetic\b", re.IGNORECASE), "empathetic"),
    (re.compile(r"\bdirect\b", re.IGNORECASE), "direct"),
]

DOMAIN_PATTERNS = [
    (re.compile(r"\b(?:write|generate|create)\s+(?:code|function|class|script|program|api|endpoint)\b", re.IGNORECASE), "technical"),
    (re.compile(r"\b(?:python|javascript|typescript|java|go|rust|sql|html|css|react)\b", re.IGNORECASE), "technical"),
    (re.compile(r"\b(?:debug|refactor|optimize|test|implement)\b", re.IGNORECASE), "technical"),
    (re.compile(r"\b(?:write|create|draft)\s+(?:a\s+|the\s+)?(?:story|poem|song|script|novel|character|world)\b", re.IGNORECASE), "creative"),
    (re.compile(r"\b(?:creative|imaginative|fiction|fantasy|sci-fi|romance|horror)\b", re.IGNORECASE), "creative"),
    (re.compile(r"\b(?:explain|describe|summarize|analyze|compare|evaluate|discuss)\b", re.IGNORECASE), "informational"),
    (re.compile(r"\b(?:research|study|report|whitepaper|article|blog|post)\b", re.IGNORECASE), "informational"),
    (re.compile(r"\b(?:business|marketing|sales|strategy|plan|proposal|pitch)\b", re.IGNORECASE), "business"),
    (re.compile(r"\b(?:medical|healthcare|clinical|patient|diagnosis|treatment)\b", re.IGNORECASE), "medical"),
    (re.compile(r"\b(?:legal|contract|law|regulation|compliance|policy)\b", re.IGNORECASE), "legal"),
]

LENGTH_PATTERNS = [
    (re.compile(r"\b(\d+)[\s\-]?(?:word|words)\b", re.IGNORECASE), "words"),
    (re.compile(r"\b(\d+)[\s\-]?(?:sentence|sentences)\b", re.IGNORECASE), "sentences"),
    (re.compile(r"\b(\d+)[\s\-]?(?:paragraph|paragraphs)\b", re.IGNORECASE), "paragraphs"),
    (re.compile(r"\b(\d+)[\s\-]?(?:line|lines)\b", re.IGNORECASE), "lines"),
    (re.compile(r"\b(?:brief|short|concise|overview)\b", re.IGNORECASE), "brief"),
    (re.compile(r"\b(?:detailed|comprehensive|thorough|in-depth|extensive)\b", re.IGNORECASE), "detailed"),
]


COMPONENT_ORDERS = {
    "informational": ["context", "task", "references", "testing", "enhancement"],
    "technical": ["task", "context", "references", "testing", "enhancement"],
    "creative": ["enhancement", "context", "task", "references", "testing"],
    "business": ["context", "task", "testing", "references", "enhancement"],
    "medical": ["context", "task", "testing", "references", "enhancement"],
    "legal": ["context", "task", "testing", "references", "enhancement"],
    "default": ["context", "task", "references", "testing", "enhancement"],
}


def _detect_implicit_signals(text: Optional[str]) -> dict:
    """Detect implicit signals in text: format, audience, tone, domain, length."""
    if not text:
        return {"formats": [], "audiences": [], "tones": [], "domains": [], "lengths": []}

    text_lower = text.lower()
    signals: dict[str, list[Any]] = {
        "formats": [],
        "audiences": [],
        "tones": [],
        "domains": [],
        "lengths": [],
    }

    for keyword, canonical in FORMAT_KEYWORDS.items():
        if keyword in text_lower and canonical not in signals["formats"]:
            signals["formats"].append(canonical)

    for pattern in AUDIENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            audience = match.group(0).strip()
            if audience not in signals["audiences"]:
                signals["audiences"].append(audience)

    for pattern, tone_name in TONE_PATTERNS:
        if pattern.search(text):
            if tone_name not in signals["tones"]:
                signals["tones"].append(tone_name)

    for pattern, domain_name in DOMAIN_PATTERNS:
        if pattern.search(text):
            if domain_name not in signals["domains"]:
                signals["domains"].append(domain_name)

    for pattern, unit in LENGTH_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1) if match.lastindex else match.group(0)
            signals["lengths"].append((value, unit))

    return signals


def _detect_implicit_components(components: dict) -> dict[str, list[Any]]:
    """Analyze all components and aggregate implicit signals."""
    all_signals: dict[str, list[Any]] = {
        "formats": [],
        "audiences": [],
        "tones": [],
        "domains": [],
        "lengths": [],
    }

    for key, value in components.items():
        if not isinstance(value, str):
            continue
        signals = _detect_implicit_signals(value)
        for signal_type, detected in signals.items():
            for item in detected:
                if item not in all_signals[signal_type]:
                    all_signals[signal_type].append(item)

    return all_signals


def _classify_prompt_type(components: dict, signals: dict) -> str:
    """Classify prompt type based on detected domain signals and content."""
    if signals["domains"]:
        priority = ["technical", "creative", "medical", "legal", "business", "informational"]
        for domain in priority:
            if domain in signals["domains"]:
                return domain

    task = components.get("task", "")
    if not task:
        return "default"

    task_lower = task.lower()

    technical_words = ["code", "function", "class", "script", "api", "debug", "refactor", "implement", "python", "javascript"]
    if any(word in task_lower for word in technical_words):
        return "technical"

    creative_words = ["story", "poem", "creative", "fiction", "character", "song", "script"]
    if any(word in task_lower for word in creative_words):
        return "creative"

    business_words = ["marketing", "sales", "strategy", "business", "proposal", "pitch"]
    if any(word in task_lower for word in business_words):
        return "business"

    return "informational"


def _select_component_order(prompt_type: str, components: dict) -> list:
    """Select optimal component ordering for the prompt type."""
    base_order = COMPONENT_ORDERS.get(prompt_type, COMPONENT_ORDERS["default"])
    present = [k for k in base_order if components.get(k) and str(components.get(k)).strip()]
    return present


def _extract_format_from_task(task: str) -> tuple[Optional[str], str]:
    """Extract explicit format specification from task text."""
    if not task:
        return None, task

    task_lower = task.lower()
    found_formats = []

    for keyword, canonical in FORMAT_KEYWORDS.items():
        if keyword in task_lower:
            found_formats.append(canonical)

    if not found_formats:
        return None, task

    cleaned = task
    for keyword in FORMAT_KEYWORDS.keys():
        patterns = [
            rf"\b(?:in|as|using|with|use)\s+{re.escape(keyword)}\s*(?:format)?\b",
            rf"\b{re.escape(keyword)}\s*(?:format|output|response)\b",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"[,\.]\s*$", "", cleaned).strip()

    return found_formats[0], cleaned


def _merge_components(components: dict, signals: dict) -> dict:
    """Merge overlapping content and resolve conflicts between components."""
    merged = dict(components)

    task = merged.get("task", "")
    if task and not merged.get("references"):
        format_name, cleaned_task = _extract_format_from_task(task)
        if format_name and format_name not in str(merged.get("references", "")).lower():
            merged["task"] = cleaned_task
            if not merged.get("references"):
                merged["references"] = f"Output format: {format_name}"

    enhancement = merged.get("enhancement", "")
    if enhancement and signals["tones"] and not merged.get("context"):
        tone_str = ", ".join(signals["tones"])
        merged["context"] = f"Tone: {tone_str}."

    testing = merged.get("testing", "")
    if signals["lengths"] and not testing:
        length_specs = [f"{value} {unit}" for value, unit in signals["lengths"]]
        if length_specs:
            merged["testing"] = f"Length: {', '.join(length_specs)}."

    return merged


def _apply_adaptive_reframing(text: Optional[str], domain_hints: Optional[list] = None) -> Optional[str]:
    """Apply expanded positive reframing with adaptive domain awareness."""
    if not text:
        return text

    if _is_critical_constraint(text):
        return text

    result = text

    for pattern, replacement in REFRAME_RULES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    for pattern, replacement in ADAPTIVE_REFRAME_RULES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    if domain_hints:
        if "technical" in domain_hints:
            result = re.sub(
                r"\bdon['\u2019]?t\s+use\s+abbreviations\b",
                "spell out all abbreviations on first use",
                result,
                flags=re.IGNORECASE,
            )
        if "medical" in domain_hints:
            result = re.sub(
                r"\bdon['\u2019]?t\s+provide\s+diagnoses\b",
                "provide general information only; recommend consulting a healthcare professional",
                result,
                flags=re.IGNORECASE,
            )

    result = re.sub(r"\bdon['']t\s+not\b", "", result, flags=re.IGNORECASE)
    result = re.sub(r"\s+", " ", result).strip()

    return result


def _is_critical_constraint(text: str) -> bool:
    """Check if text contains a critical negative constraint that should not be reframed.

    Safety and compliance constraints (e.g., "Never share personal information")
    must be preserved exactly as written and not converted to positive framing.

    Args:
        text: Input text to check.

    Returns:
        True if the text contains a critical negative constraint pattern.
    """
    for pattern in _CRITICAL_CONSTRAINT_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def _apply_reframing(text: Optional[str]) -> Optional[str]:
    """Convert negative constraints in text to positive specifications.

    Uses a rule-based approach to detect common negative constraint patterns
    and replace them with positive, actionable instructions.

    Critical safety/compliance constraints (e.g., "Never share personal
    information") are detected and preserved unchanged.

    Args:
        text: Input text that may contain negative constraints. None is
            returned unchanged.

    Returns:
        Text with negative constraints reframed as positive specifications,
        or the original text if it contains critical safety constraints,
        or None if the input was None.
    """
    if not text:
        return text

    if _is_critical_constraint(text):
        return text

    result = text
    for pattern, replacement in REFRAME_RULES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    result = re.sub(r"\bdon['']t\s+not\b", "", result, flags=re.IGNORECASE)
    result = re.sub(r"\s+", " ", result).strip()

    return result


def _format_markdown_adaptive(
    components: dict,
    order: list,
    signals: dict,
) -> str:
    """Assemble components in Markdown format with adaptive ordering and reframing."""
    sections = []
    section_labels = {
        "context": "Context",
        "task": "Task",
        "references": "References",
        "testing": "Testing",
        "enhancement": "Enhancement",
    }

    for key in order:
        text = components.get(key)
        if text and text.strip():
            reframed = _apply_adaptive_reframing(text, signals.get("domains"))
            sections.append(f"## {section_labels[key]}\n\n{reframed}")

    return "\n\n".join(sections)


def _format_xml_adaptive(
    components: dict,
    order: list,
    signals: dict,
) -> str:
    """Assemble components in XML format with adaptive ordering and reframing."""
    sections = ["<prompt>"]

    for key in order:
        text = components.get(key)
        if text and text.strip():
            reframed = _apply_adaptive_reframing(text, signals.get("domains"))
            escaped = xmlutils.escape(reframed or "")
            sections.append(f"<{key}>\n{escaped}\n</{key}>")

    sections.append("</prompt>")
    return "\n\n".join(sections)


def _format_markdown(
    context: Optional[str],
    task: Optional[str],
    references: Optional[str],
    testing: Optional[str],
    enhancement: Optional[str],
) -> str:
    """Assemble components in Markdown format.

    Args:
        context: Context component (audience, purpose, constraints).
        task: Task component (action-oriented description).
        references: References component (examples, templates).
        testing: Testing component (success criteria).
        enhancement: Enhancement component (tone, iteration notes).

    Returns:
        Assembled prompt string in Markdown format.
    """
    sections = []

    if context:
        sections.append(f"## Context\n\n{_apply_reframing(context)}")

    if task:
        sections.append(f"## Task\n\n{_apply_reframing(task)}")

    if references:
        sections.append(f"## References\n\n{_apply_reframing(references)}")

    if testing:
        sections.append(f"## Testing\n\n{_apply_reframing(testing)}")

    if enhancement:
        sections.append(f"## Enhancement\n\n{_apply_reframing(enhancement)}")

    return "\n\n".join(sections)


def _format_xml(
    context: Optional[str],
    task: Optional[str],
    references: Optional[str],
    testing: Optional[str],
    enhancement: Optional[str],
) -> str:
    """Assemble components in XML format.

    XML tags provide unambiguous section boundaries for complex multi-section prompts.

    Args:
        context: Context component (audience, purpose, constraints).
        task: Task component (action-oriented description).
        references: References component (examples, templates).
        testing: Testing component (success criteria).
        enhancement: Enhancement component (tone, iteration notes).

    Returns:
        Assembled prompt string in XML format.
    """
    sections = ["<prompt>"]

    if context:
        sections.append(f"<context>\n{xmlutils.escape(_apply_reframing(context) or '')}\n</context>")

    if task:
        sections.append(f"<task>\n{xmlutils.escape(_apply_reframing(task) or '')}\n</task>")

    if references:
        sections.append(f"<references>\n{xmlutils.escape(_apply_reframing(references) or '')}\n</references>")

    if testing:
        sections.append(f"<testing>\n{xmlutils.escape(_apply_reframing(testing) or '')}\n</testing>")

    if enhancement:
        sections.append(f"<enhancement>\n{xmlutils.escape(_apply_reframing(enhancement) or '')}\n</enhancement>")

    sections.append("</prompt>")

    return "\n\n".join(sections)


def assemble(components: dict, format_type: str = "markdown", adaptive: bool = False) -> str:
    """Assemble TCRTE components into a production-ready prompt.

    Components are assembled in strict TCRTE order:
    Context → Task → References → Testing → Enhancement.

    Negative constraints are automatically reframed as positive specifications
    to avoid the "Pink Elephant" effect where telling a model what NOT to do
    increases the probability it will do exactly that.

    Args:
        components: Dictionary with keys: task, context, references, testing, enhancement.
            Each value should be a string describing that component.
            Missing keys or None values are handled gracefully (omitted from output).
        format_type: Output format. Supported values:
            - "markdown" (default): Simple human-editable format with ## headers.
            - "xml": Structured format with XML tags for complex multi-section prompts.
        adaptive: If True, enables adaptive assembly that detects implicit signals,
            selects optimal component ordering, resolves overlaps, and applies
            domain-aware reframing. Default is False for backward compatibility.

    Returns:
        Assembled prompt string in the requested format.

    Raises:
        ValueError: If format_type is not "markdown" or "xml".

    Examples:
        >>> components = {
        ...     "task": "Write product descriptions for seniors browsing an e-commerce site.",
        ...     "context": "Audience: seniors (65+). Purpose: drive conversions.",
        ... }
        >>> prompt = assemble(components, format_type="markdown")
        >>> "## Context" in prompt
        True

        >>> components = {
        ...     "task": "Don't be verbose. Write about cats.",
        ...     "context": "Pet owners looking for care tips.",
        ... }
        >>> prompt = assemble(components)
        >>> "don't" in prompt.lower()
        False
        >>> "conciseness" in prompt.lower()
        True
    """
    if format_type not in ("markdown", "xml"):
        raise ValueError(
            f"Unsupported format_type: {format_type!r}. "
            "Supported formats: 'markdown', 'xml'."
        )

    if not isinstance(components, dict):
        raise TypeError(f"components must be dict, got {type(components).__name__}")

    context = components.get("context")
    task = components.get("task")
    references = components.get("references")
    testing = components.get("testing")
    enhancement = components.get("enhancement")

    for name, value in [
        ("context", context),
        ("task", task),
        ("references", references),
        ("testing", testing),
        ("enhancement", enhancement),
    ]:
        if value is not None and not isinstance(value, str):
            raise TypeError(
                f"Component '{name}' must be str or None, got {type(value).__name__}"
            )

    context = context.strip() if context and context.strip() else None
    task = task.strip() if task and task.strip() else None
    references = references.strip() if references and references.strip() else None
    testing = testing.strip() if testing and testing.strip() else None
    enhancement = enhancement.strip() if enhancement and enhancement.strip() else None

    if adaptive:
        cleaned_components = {
            "context": context,
            "task": task,
            "references": references,
            "testing": testing,
            "enhancement": enhancement,
        }
        signals = _detect_implicit_components(cleaned_components)
        merged = _merge_components(cleaned_components, signals)
        prompt_type = _classify_prompt_type(merged, signals)
        order = _select_component_order(prompt_type, merged)

        if format_type == "markdown":
            return _format_markdown_adaptive(merged, order, signals)
        return _format_xml_adaptive(merged, order, signals)

    if format_type == "markdown":
        return _format_markdown(context, task, references, testing, enhancement)
    return _format_xml(context, task, references, testing, enhancement)


def main():
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Assemble TCRTE components into a prompt")
    parser.add_argument("components", help="JSON object with TCRTE components")
    parser.add_argument(
        "--format",
        choices=["markdown", "xml"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--adaptive",
        action="store_true",
        help="Enable adaptive assembly with signal detection and optimal ordering",
    )
    args = parser.parse_args()

    try:
        comp = json.loads(args.components)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(comp, dict):
        print("Error: JSON must be an object/dictionary", file=sys.stderr)
        sys.exit(1)

    print(assemble(comp, args.format, adaptive=args.adaptive))


if __name__ == "__main__":
    main()
