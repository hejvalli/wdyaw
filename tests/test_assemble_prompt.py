import pytest
from wdyaw.scripts.assemble_prompt import (
    assemble,
    _apply_reframing,
    _detect_implicit_signals,
    _classify_prompt_type,
    _select_component_order,
    _extract_format_from_task,
    _merge_components,
    _apply_adaptive_reframing,
)


class TestAssemblePromptMarkdown:
    """Tests for markdown format assembly."""

    def test_markdown_assembly_with_all_components(self):
        """Should assemble all components in markdown format."""
        components = {
            "context": "Audience: seniors",
            "task": "Write product descriptions",
            "references": "Example: Best Buy style",
            "testing": "Must include price and features",
            "enhancement": "Use warm, friendly tone",
        }
        result = assemble(components, format_type="markdown")
        assert "## Context" in result
        assert "## Task" in result
        assert "## References" in result
        assert "## Testing" in result
        assert "## Enhancement" in result
        assert "Audience: seniors" in result
        assert "Write product descriptions" in result

    def test_markdown_assembly_with_partial_components(self):
        """Should assemble only provided components."""
        components = {
            "context": "Test context",
            "task": "Test task",
        }
        result = assemble(components, format_type="markdown")
        assert "## Context" in result
        assert "## Task" in result
        assert "## References" not in result
        assert "## Testing" not in result
        assert "## Enhancement" not in result

    def test_markdown_assembly_with_empty_components(self):
        """Should return empty string when no components provided."""
        components = {}
        result = assemble(components, format_type="markdown")
        assert result == ""

    def test_markdown_assembly_with_none_values(self):
        """Should skip None values in components."""
        components = {
            "context": "Test context",
            "task": None,
            "references": "",
        }
        result = assemble(components, format_type="markdown")
        assert "## Context" in result
        assert "## Task" not in result
        assert "## References" not in result

    def test_markdown_tcrte_order_maintained(self):
        """TCRTE order should be maintained in markdown output."""
        components = {
            "enhancement": "Enhancement first",
            "testing": "Testing second",
            "references": "References third",
            "task": "Task fourth",
            "context": "Context fifth",
        }
        result = assemble(components, format_type="markdown")
        context_pos = result.find("## Context")
        task_pos = result.find("## Task")
        refs_pos = result.find("## References")
        testing_pos = result.find("## Testing")
        enhancement_pos = result.find("## Enhancement")
        assert context_pos < task_pos < refs_pos < testing_pos < enhancement_pos


class TestAssemblePromptXML:
    """Tests for XML format assembly."""

    def test_xml_assembly_with_all_components(self):
        """Should assemble all components in XML format."""
        components = {
            "context": "Audience: seniors",
            "task": "Write product descriptions",
            "references": "Example: Best Buy style",
            "testing": "Must include price and features",
            "enhancement": "Use warm, friendly tone",
        }
        result = assemble(components, format_type="xml")
        assert "<prompt>" in result
        assert "</prompt>" in result
        assert "<context>" in result
        assert "</context>" in result
        assert "<task>" in result
        assert "</task>" in result
        assert "<references>" in result
        assert "</references>" in result
        assert "<testing>" in result
        assert "</testing>" in result
        assert "<enhancement>" in result
        assert "</enhancement>" in result

    def test_xml_assembly_with_partial_components(self):
        """Should assemble only provided components in XML."""
        components = {
            "context": "Test context",
            "task": "Test task",
        }
        result = assemble(components, format_type="xml")
        assert "<context>" in result
        assert "<task>" in result
        assert "<references>" not in result
        assert "<testing>" not in result
        assert "<enhancement>" not in result

    def test_xml_assembly_empty_components(self):
        """Should return minimal XML when no components provided."""
        components = {}
        result = assemble(components, format_type="xml")
        assert result == "<prompt>\n\n</prompt>"

    def test_xml_tcrte_order_maintained(self):
        """TCRTE order should be maintained in XML output."""
        components = {
            "enhancement": "Enhancement first",
            "testing": "Testing second",
            "references": "References third",
            "task": "Task fourth",
            "context": "Context fifth",
        }
        result = assemble(components, format_type="xml")
        context_pos = result.find("<context>")
        task_pos = result.find("<task>")
        refs_pos = result.find("<references>")
        testing_pos = result.find("<testing>")
        enhancement_pos = result.find("<enhancement>")
        assert context_pos < task_pos < refs_pos < testing_pos < enhancement_pos


class TestAssemblePromptCriticalConstraints:
    """Tests for preserving critical safety/compliance constraints."""

    def test_critical_constraint_preserved_never_share_pii(self):
        """Should preserve 'never share personal information' unchanged."""
        text = "Never share personal information or medical advice"
        result = _apply_reframing(text)
        assert result == text

    def test_critical_constraint_preserved_do_not_provide_advice(self):
        """Should preserve 'do not provide medical advice' unchanged."""
        text = "Do not provide medical advice"
        result = _apply_reframing(text)
        assert result == text

    def test_critical_constraint_preserved_strictly_prohibited(self):
        """Should preserve 'strictly prohibited' unchanged."""
        text = "Strictly prohibited content"
        result = _apply_reframing(text)
        assert result == text

    def test_critical_constraint_in_full_assembly(self):
        """Critical constraints should survive full assembly."""
        components = {
            "task": "Generate a response. Never share personal information.",
            "context": "Healthcare chatbot.",
        }
        result = assemble(components, format_type="markdown")
        assert "Never share personal information" in result
        assert "don't" not in result.lower()

    def test_non_critical_still_reframed(self):
        """Non-critical constraints should still be reframed."""
        text = "Don't be verbose in your response"
        result = _apply_reframing(text)
        assert "don't" not in result.lower()
        assert "conciseness" in result.lower()


class TestAssemblePromptReframing:
    """Tests for positive reframing of negative constraints."""

    def test_reframe_dont_be_verbose(self):
        """Should reframe 'don't be verbose' to positive statement."""
        text = "Don't be verbose in your response"
        result = _apply_reframing(text)
        assert "don't" not in result.lower()
        assert "conciseness" in result.lower()

    def test_reframe_dont_use_jargon(self):
        """Should reframe 'don't use jargon' to positive statement."""
        text = "Don't use jargon"
        result = _apply_reframing(text)
        assert "don't" not in result.lower()
        assert "simple" in result.lower()

    def test_reframe_dont_include_fluff(self):
        """Should reframe 'don't include fluff' to positive statement."""
        text = "Don't include fluff"
        result = _apply_reframing(text)
        assert "don't" not in result.lower()
        assert "core argument" in result.lower()

    def test_reframe_dont_make_assumptions(self):
        """Should reframe 'don't make assumptions' to positive statement."""
        text = "Don't make assumptions"
        result = _apply_reframing(text)
        assert "don't" not in result.lower()
        assert "clarification" in result.lower()

    def test_reframe_avoid_technical_terms(self):
        """Should reframe 'avoid technical terms' to positive statement."""
        text = "Avoid technical terms"
        result = _apply_reframing(text)
        assert "avoid" not in result.lower()
        assert "accessible" in result.lower()

    def test_reframe_never_be_verbose(self):
        """Should reframe 'never be verbose' to positive statement."""
        text = "Never be verbose"
        result = _apply_reframing(text)
        assert "never" not in result.lower()
        assert "conciseness" in result.lower()

    def test_reframe_never_use_jargon(self):
        """Should reframe 'never use jargon' to positive statement."""
        text = "Never use jargon"
        result = _apply_reframing(text)
        assert "never" not in result.lower()
        assert "simple" in result.lower()

    def test_reframe_preserve_surrounding_text(self):
        """Should preserve surrounding text when reframing."""
        text = "Please don't be verbose and provide clear answers"
        result = _apply_reframing(text)
        assert "Please" in result
        assert "provide clear answers" in result
        assert "don't" not in result.lower()

    def test_reframe_no_match_returns_original(self):
        """Should return original text when no reframing rules match."""
        text = "Write a detailed analysis"
        result = _apply_reframing(text)
        assert result == text

    def test_reframe_empty_string(self):
        """Should handle empty string gracefully."""
        result = _apply_reframing("")
        assert result == ""

    def test_reframe_none_returns_none(self):
        """Should handle None gracefully."""
        result = _apply_reframing(None)
        assert result is None

    def test_reframe_dont_without_apostrophe(self):
        """Should reframe 'dont' (no apostrophe) as well."""
        text = "Dont be verbose in your response"
        result = _apply_reframing(text)
        assert "dont" not in result.lower()
        assert "conciseness" in result.lower()

    def test_reframe_case_insensitive(self):
        """Should match patterns case-insensitively."""
        text = "DON'T BE VERBOSE"
        result = _apply_reframing(text)
        assert "DON'T" not in result
        assert "conciseness" in result.lower()

    def test_reframe_cleans_double_negatives(self):
        """Should clean up double negatives."""
        text = "Don't not include examples"
        result = _apply_reframing(text)
        assert "don't not" not in result.lower()

    def test_reframe_in_full_assembly(self):
        """Reframing should be applied during full assembly."""
        components = {
            "task": "Don't be verbose. Write about cats.",
            "context": "Pet owners looking for care tips.",
        }
        result = assemble(components, format_type="markdown")
        assert "don't" not in result.lower()
        assert "conciseness" in result.lower()
        assert "Write about cats" in result

    def test_reframe_multiple_rules_same_text(self):
        """Should apply multiple different reframing rules to same text."""
        text = "Don't be verbose and don't use jargon"
        result = _apply_reframing(text)
        assert "don't" not in result.lower()
        assert "conciseness" in result.lower()
        assert "simple" in result.lower()

    def test_reframe_non_string_falsy_values(self):
        """Should raise TypeError or return unchanged for non-string falsy values."""
        result_zero = _apply_reframing(0)
        assert result_zero == 0
        result_false = _apply_reframing(False)
        assert result_false is False
        result_empty_list = _apply_reframing([])
        assert result_empty_list == []


class TestAssemblePromptInvalidFormat:
    """Tests for invalid format handling."""

    def test_invalid_format_raises_valueerror(self):
        """Should raise ValueError for unsupported format type."""
        components = {"task": "Write about cats"}
        with pytest.raises(ValueError, match="Unsupported format_type"):
            assemble(components, format_type="yaml")

    def test_invalid_format_uppercase_raises_valueerror(self):
        """Should raise ValueError for uppercase format type."""
        components = {"task": "Write about cats"}
        with pytest.raises(ValueError, match="Unsupported format_type"):
            assemble(components, format_type="MARKDOWN")

    def test_invalid_format_empty_string_raises_valueerror(self):
        """Should raise ValueError for empty string format type."""
        components = {"task": "Write about cats"}
        with pytest.raises(ValueError, match="Unsupported format_type"):
            assemble(components, format_type="")


class TestAssemblePromptEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_missing_components_handled(self):
        """Should handle missing component keys gracefully."""
        components = {"task": "Only task provided"}
        result = assemble(components, format_type="markdown")
        assert "## Task" in result
        assert "## Context" not in result

    def test_none_component_values_omitted(self):
        """None values should be omitted from output."""
        components = {
            "context": None,
            "task": "Valid task",
            "references": None,
        }
        result = assemble(components, format_type="markdown")
        assert "## Task" in result
        assert "## Context" not in result
        assert "## References" not in result

    def test_empty_string_component_values_omitted(self):
        """Empty string values should be omitted from output."""
        components = {
            "context": "",
            "task": "Valid task",
            "references": "",
        }
        result = assemble(components, format_type="markdown")
        assert "## Task" in result
        assert "## Context" not in result
        assert "## References" not in result

    def test_default_format_is_markdown(self):
        """Default format should be markdown."""
        components = {"task": "Write about dogs"}
        result = assemble(components)
        assert "## Task" in result
        assert "<task>" not in result

    def test_component_with_newlines(self):
        """Should preserve newlines within component content."""
        components = {
            "task": "Line one\nLine two\nLine three",
        }
        result = assemble(components, format_type="markdown")
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result

    def test_component_with_special_chars(self):
        """Should handle special characters in components."""
        components = {
            "task": "Use JSON: {\"key\": \"value\"}",
        }
        result = assemble(components, format_type="markdown")
        assert "{\"key\": \"value\"}" in result

    def test_xml_escapes_special_chars(self):
        """Should escape XML special characters in XML format."""
        components = {
            "task": "Use JSON: <script>alert(1)</script>",
        }
        result = assemble(components, format_type="xml")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        assert "<task>" in result

    def test_whitespace_only_components_omitted(self):
        """Whitespace-only component values should be omitted from output."""
        components = {
            "context": "   ",
            "task": "Valid task",
        }
        result = assemble(components, format_type="markdown")
        assert "## Context" not in result
        assert "## Task" in result

    def test_list_components_raises_typeerror(self):
        """Should raise TypeError for non-dict components."""
        with pytest.raises(TypeError, match="components must be dict"):
            assemble(["not", "a", "dict"])

    def test_int_component_value_raises_typeerror(self):
        with pytest.raises(TypeError, match="Component 'task' must be str or None"):
            assemble({"task": 123})

    def test_bool_component_value_raises_typeerror(self):
        with pytest.raises(TypeError, match="Component 'context' must be str or None"):
            assemble({"context": True, "task": "Valid task"})

    def test_large_component_text(self):
        """Should handle large component text."""
        components = {
            "task": "Write about cats " * 100,
        }
        result = assemble(components, format_type="markdown")
        assert "## Task" in result
        assert len(result) > 1000


class TestAssemblePromptCLI:
    """Tests for the CLI/main block."""

    def test_main_with_json_argument(self, capsys, monkeypatch):
        """Should accept JSON components as argument."""
        import runpy
        monkeypatch.setattr(
            "sys.argv",
            ["assemble_prompt.py", '{"task":"Write about cats"}', "--format", "markdown"],
        )
        runpy.run_module("wdyaw.scripts.assemble_prompt", run_name="__main__")
        captured = capsys.readouterr()
        assert "## Task" in captured.out

    def test_main_with_invalid_json(self, capsys, monkeypatch):
        """Should handle invalid JSON input."""
        import runpy
        monkeypatch.setattr(
            "sys.argv",
            ["assemble_prompt.py", "not-json", "--format", "markdown"],
        )
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("wdyaw.scripts.assemble_prompt", run_name="__main__")
        assert exc_info.value.code == 1

    def test_main_no_args_prints_usage(self, capsys, monkeypatch):
        """Should print usage when no arguments provided."""
        import runpy
        monkeypatch.setattr("sys.argv", ["assemble_prompt.py"])
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("wdyaw.scripts.assemble_prompt", run_name="__main__")
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "usage:" in captured.err.lower()


class TestAdaptiveAssembly:
    """Tests for adaptive assembly mode."""

    def test_adaptive_technical_prompt_task_first(self):
        """Technical prompts should put Task before Context."""
        components = {
            "task": "Write a Python function to filter active users",
            "context": "For a REST API backend",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        task_pos = result.find("## Task")
        context_pos = result.find("## Context")
        assert task_pos < context_pos

    def test_adaptive_creative_prompt_enhancement_first(self):
        """Creative prompts should put Enhancement before Context."""
        components = {
            "task": "Write a short story about space exploration",
            "enhancement": "Tone: mysterious and awe-inspiring",
            "context": "For a sci-fi anthology",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        enhancement_pos = result.find("## Enhancement")
        context_pos = result.find("## Context")
        task_pos = result.find("## Task")
        assert enhancement_pos < context_pos < task_pos

    def test_adaptive_informational_prompt_context_first(self):
        """Informational prompts should keep Context before Task."""
        components = {
            "task": "Explain quantum computing",
            "context": "For high school students",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        context_pos = result.find("## Context")
        task_pos = result.find("## Task")
        assert context_pos < task_pos

    def test_adaptive_extracts_format_from_task(self):
        """Should extract format specification from task into references."""
        components = {
            "task": "Write a summary in JSON format about cats",
            "context": "Pet owners",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        assert "## References" in result
        assert "json" in result.lower()
        assert "in JSON format" not in result  # Should be extracted from task

    def test_adaptive_detects_tone_in_enhancement(self):
        """Should detect tone in enhancement and merge into context if no context."""
        components = {
            "task": "Write about cats",
            "enhancement": "Professional tone",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        assert "## Context" in result
        assert "professional" in result.lower()

    def test_adaptive_detects_length_constraints(self):
        """Should detect length constraints and add to testing."""
        components = {
            "task": "Write a 200-word summary about cats",
            "context": "Pet owners",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        assert "## Testing" in result
        assert "200" in result
        assert "words" in result.lower()

    def test_adaptive_reframing_indirect_negation(self):
        """Should reframe indirect negation patterns."""
        text = "Refrain from using technical jargon"
        result = _apply_adaptive_reframing(text)
        assert "refrain from" not in result.lower()
        assert "alternative approaches" in result.lower()

    def test_adaptive_reframing_skip_omit(self):
        """Should reframe skip/omit patterns."""
        text = "Skip the introduction and omit personal details"
        result = _apply_adaptive_reframing(text)
        assert "skip" not in result.lower()
        assert "omit" not in result.lower()

    def test_adaptive_domain_aware_technical(self):
        """Should apply domain-aware reframing for technical prompts."""
        text = "Don't use abbreviations in the documentation"
        result = _apply_adaptive_reframing(text, domain_hints=["technical"])
        assert "don't" not in result.lower()
        assert "spell out" in result.lower()

    def test_adaptive_domain_aware_medical(self):
        """Should apply domain-aware reframing for medical prompts."""
        text = "Don't provide diagnoses to patients"
        result = _apply_adaptive_reframing(text, domain_hints=["medical"])
        assert "don't" not in result.lower()
        assert "consulting a healthcare professional" in result.lower()

    def test_adaptive_critical_constraint_preserved(self):
        """Critical constraints should still be preserved in adaptive mode."""
        components = {
            "task": "Generate advice. Never share personal information.",
            "context": "Healthcare chatbot.",
        }
        result = assemble(components, format_type="markdown", adaptive=True)
        assert "Never share personal information" in result

    def test_adaptive_xml_format(self):
        """Adaptive mode should work with XML output."""
        components = {
            "task": "Write a Python function in JSON format",
            "context": "For backend developers",
        }
        result = assemble(components, format_type="xml", adaptive=True)
        assert "<prompt>" in result
        assert "<task>" in result
        assert "<context>" in result
        assert "<references>" in result

    def test_adaptive_backward_compatibility(self):
        """Default behavior should remain unchanged (non-adaptive)."""
        components = {
            "task": "Write a Python function",
            "context": "For backend developers",
        }
        result_default = assemble(components, format_type="markdown")
        result_explicit = assemble(components, format_type="markdown", adaptive=False)
        assert result_default == result_explicit
        assert "## Context" in result_default
        assert result_default.find("## Context") < result_default.find("## Task")

    def test_adaptive_cli_flag(self, capsys, monkeypatch):
        """CLI should support --adaptive flag."""
        import runpy
        monkeypatch.setattr(
            "sys.argv",
            [
                "assemble_prompt.py",
                '{"task":"Write a Python function","context":"For developers"}',
                "--format",
                "markdown",
                "--adaptive",
            ],
        )
        runpy.run_module("wdyaw.scripts.assemble_prompt", run_name="__main__")
        captured = capsys.readouterr()
        assert "## Task" in captured.out
        assert "## Context" in captured.out


class TestImplicitSignalDetection:
    """Tests for implicit signal detection functions."""

    def test_detect_format_json(self):
        signals = _detect_implicit_signals("Return the result in JSON format")
        assert "json" in signals["formats"]

    def test_detect_format_bullet_points(self):
        signals = _detect_implicit_signals("Use bullet points for the list")
        assert "bullet points" in signals["formats"]

    def test_detect_audience_seniors(self):
        signals = _detect_implicit_signals("Write for seniors about technology")
        assert any("seniors" in aud for aud in signals["audiences"])

    def test_detect_audience_target(self):
        signals = _detect_implicit_signals("Target audience: developers")
        assert any("audience" in aud.lower() for aud in signals["audiences"])

    def test_detect_tone_professional(self):
        signals = _detect_implicit_signals("Use a professional tone")
        assert "professional" in signals["tones"]

    def test_detect_tone_multiple(self):
        signals = _detect_implicit_signals("Be friendly but professional")
        assert "friendly" in signals["tones"]
        assert "professional" in signals["tones"]

    def test_detect_domain_technical(self):
        signals = _detect_implicit_signals("Write a Python function to sort data")
        assert "technical" in signals["domains"]

    def test_detect_domain_creative(self):
        signals = _detect_implicit_signals("Write a story about dragons")
        assert "creative" in signals["domains"]

    def test_detect_domain_medical(self):
        signals = _detect_implicit_signals("Explain the diagnosis process")
        assert "medical" in signals["domains"]

    def test_detect_length_words(self):
        signals = _detect_implicit_signals("Write exactly 500 words")
        assert ("500", "words") in signals["lengths"]

    def test_detect_length_brief(self):
        signals = _detect_implicit_signals("Keep it brief and concise")
        assert any(unit == "brief" for _, unit in signals["lengths"])

    def test_detect_empty_text(self):
        signals = _detect_implicit_signals("")
        assert signals == {"formats": [], "audiences": [], "tones": [], "domains": [], "lengths": []}

    def test_detect_none_text(self):
        signals = _detect_implicit_signals(None)
        assert signals == {"formats": [], "audiences": [], "tones": [], "domains": [], "lengths": []}


class TestPromptTypeClassification:
    """Tests for prompt type classification."""

    def test_classify_technical_from_domain(self):
        components = {"task": "Write code", "context": "Python project"}
        signals = {"domains": ["technical"], "formats": [], "audiences": [], "tones": [], "lengths": []}
        assert _classify_prompt_type(components, signals) == "technical"

    def test_classify_creative_from_task(self):
        components = {"task": "Write a poem about nature"}
        signals = {"domains": [], "formats": [], "audiences": [], "tones": [], "lengths": []}
        assert _classify_prompt_type(components, signals) == "creative"

    def test_classify_business_from_task(self):
        components = {"task": "Create a marketing strategy"}
        signals = {"domains": [], "formats": [], "audiences": [], "tones": [], "lengths": []}
        assert _classify_prompt_type(components, signals) == "business"

    def test_classify_informational_fallback(self):
        components = {"task": "Explain photosynthesis"}
        signals = {"domains": [], "formats": [], "audiences": [], "tones": [], "lengths": []}
        assert _classify_prompt_type(components, signals) == "informational"

    def test_classify_default_empty_task(self):
        components = {}
        signals = {"domains": [], "formats": [], "audiences": [], "tones": [], "lengths": []}
        assert _classify_prompt_type(components, signals) == "default"

    def test_classify_priority_technical_over_informational(self):
        components = {"task": "Explain code"}
        signals = {"domains": ["technical", "informational"], "formats": [], "audiences": [], "tones": [], "lengths": []}
        assert _classify_prompt_type(components, signals) == "technical"


class TestComponentOrdering:
    """Tests for component ordering selection."""

    def test_technical_order(self):
        components = {
            "context": "Backend API",
            "task": "Write function",
            "references": "Example code",
        }
        order = _select_component_order("technical", components)
        assert order == ["task", "context", "references"]

    def test_creative_order(self):
        components = {
            "enhancement": "Mysterious tone",
            "context": "Fantasy world",
            "task": "Write story",
        }
        order = _select_component_order("creative", components)
        assert order == ["enhancement", "context", "task"]

    def test_filters_missing_components(self):
        components = {"task": "Only task"}
        order = _select_component_order("informational", components)
        assert order == ["task"]

    def test_default_order(self):
        components = {
            "context": "Test",
            "task": "Test",
            "references": "Test",
            "testing": "Test",
            "enhancement": "Test",
        }
        order = _select_component_order("default", components)
        assert order == ["context", "task", "references", "testing", "enhancement"]


class TestFormatExtraction:
    """Tests for format extraction from task text."""

    def test_extract_json_format(self):
        format_name, cleaned = _extract_format_from_task("Write in JSON format")
        assert format_name == "json"
        assert "JSON" not in cleaned

    def test_extract_bullet_points(self):
        format_name, cleaned = _extract_format_from_task("Use bullet points for the list")
        assert format_name == "bullet points"
        assert "bullet points" not in cleaned.lower()

    def test_no_format_found(self):
        format_name, cleaned = _extract_format_from_task("Write about cats")
        assert format_name is None
        assert cleaned == "Write about cats"

    def test_extract_with_as_keyword(self):
        format_name, cleaned = _extract_format_from_task("Return as markdown")
        assert format_name == "markdown"
        assert "as markdown" not in cleaned.lower()

    def test_empty_task(self):
        format_name, cleaned = _extract_format_from_task("")
        assert format_name is None
        assert cleaned == ""


class TestComponentMerging:
    """Tests for component merging logic."""

    def test_merge_format_into_references(self):
        components = {"task": "Write in JSON format", "context": "Test"}
        signals = {"formats": ["json"], "audiences": [], "tones": [], "domains": [], "lengths": []}
        merged = _merge_components(components, signals)
        assert merged["references"] == "Output format: json"
        assert "JSON format" not in merged["task"]

    def test_merge_tone_into_context(self):
        components = {"task": "Write", "enhancement": "Professional"}
        signals = {"formats": [], "audiences": [], "tones": ["professional"], "domains": [], "lengths": []}
        merged = _merge_components(components, signals)
        assert merged["context"] == "Tone: professional."

    def test_merge_length_into_testing(self):
        components = {"task": "Write 500 words", "context": "Test"}
        signals = {"formats": [], "audiences": [], "tones": [], "domains": [], "lengths": [("500", "words")]}
        merged = _merge_components(components, signals)
        assert merged["testing"] == "Length: 500 words."

    def test_no_merge_when_references_exists(self):
        components = {"task": "Write in JSON format", "references": "Already have format"}
        signals = {"formats": ["json"], "audiences": [], "tones": [], "domains": [], "lengths": []}
        merged = _merge_components(components, signals)
        assert merged["references"] == "Already have format"

    def test_no_merge_when_context_exists(self):
        components = {"task": "Write", "context": "Already exists", "enhancement": "Professional"}
        signals = {"formats": [], "audiences": [], "tones": ["professional"], "domains": [], "lengths": []}
        merged = _merge_components(components, signals)
        assert merged["context"] == "Already exists"

    def test_no_merge_when_testing_exists(self):
        components = {"task": "Write 500 words", "testing": "Already exists"}
        signals = {"formats": [], "audiences": [], "tones": [], "domains": [], "lengths": [("500", "words")]}
        merged = _merge_components(components, signals)
        assert merged["testing"] == "Already exists"


class TestAdaptiveReframing:
    """Tests for adaptive reframing with expanded rules."""

    def test_refrain_from_using(self):
        result = _apply_adaptive_reframing("Refrain from using complex terms")
        assert "refrain from" not in result.lower()
        assert "alternative approaches" in result.lower()

    def test_steer_clear_of(self):
        result = _apply_adaptive_reframing("Steer clear of technical jargon")
        assert "steer clear of" not in result.lower()

    def test_skip_the(self):
        result = _apply_adaptive_reframing("Skip the introduction")
        assert "skip" not in result.lower()
        assert "proceed directly" in result.lower()

    def test_omit_the(self):
        result = _apply_adaptive_reframing("Omit the conclusion")
        assert "omit" not in result.lower()
        assert "exclude" in result.lower()

    def test_leave_out(self):
        result = _apply_adaptive_reframing("Leave out personal details")
        assert "leave out" not in result.lower()
        assert "exclude" in result.lower()

    def test_dont_be_repetitive(self):
        result = _apply_adaptive_reframing("Don't be repetitive")
        assert "don't" not in result.lower()
        assert "adds new information" in result.lower()

    def test_never_repeat_yourself(self):
        result = _apply_adaptive_reframing("Never repeat yourself")
        assert "never" not in result.lower()
        assert "adds new information" in result.lower()

    def test_critical_constraint_still_preserved(self):
        text = "Never share personal information"
        result = _apply_adaptive_reframing(text)
        assert result == text

    def test_none_returns_none(self):
        assert _apply_adaptive_reframing(None) is None

    def test_empty_string_returns_empty(self):
        assert _apply_adaptive_reframing("") == ""
