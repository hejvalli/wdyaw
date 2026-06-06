import pytest
from wdyaw.scripts.validate_prompt import (
    validate,
    _detect_p01,
    _detect_p02,
    _detect_p03,
    _calculate_score,
    _classify_p01_severity,
)


class TestValidatePromptP01SeverityClassification:
    """Tests for P01 severity classification (critical/warning/error)."""

    def test_critical_never_reveal_personal_info(self):
        """Should classify 'never reveal personal information' as critical."""
        text = "Never reveal personal information"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["severity_counts"]["critical"] == 1
        assert result["details"]["severity_counts"]["error"] == 0

    def test_critical_do_not_provide_medical_advice(self):
        """Should classify 'do not provide medical advice' as critical."""
        text = "Do not provide medical advice"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "critical"

    def test_critical_do_not_share_confidential_data(self):
        """Should classify 'do not share confidential data' as critical."""
        text = "Do not share confidential data"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "critical"

    def test_critical_never_fabricate_statistics(self):
        """Should classify 'never fabricate statistics' as critical."""
        text = "Never fabricate statistics"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "critical"

    def test_critical_must_not_share(self):
        """Should classify 'must not share' as critical."""
        text = "You must not share this"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "critical"

    def test_critical_strictly_prohibited(self):
        """Should classify 'strictly prohibited' as critical."""
        text = "This is strictly prohibited"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "critical"

    def test_critical_banned_phrases(self):
        """Should classify 'banned phrases' as critical."""
        text = "These are banned phrases"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "critical"

    def test_warning_avoid_technical_jargon(self):
        """Should classify 'avoid technical jargon' as warning."""
        text = "Avoid technical jargon in your response"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "warning"

    def test_warning_never_include_introduction(self):
        """Should classify 'never include an introduction' as warning."""
        text = "Never include an introduction"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["matches"][0]["severity"] == "warning"

    def test_error_dont_be_bad(self):
        """Should classify 'don't be bad' as error."""
        text = "Don't be bad"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["matches"][0]["severity"] == "error"

    def test_error_never_make_mistakes(self):
        """Should classify 'never make mistakes' as error."""
        text = "Never make mistakes"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["matches"][0]["severity"] == "error"

    def test_error_fallback_vague_negative(self):
        """Should classify vague negatives as error (fallback)."""
        text = "Don't be verbose"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["matches"][0]["severity"] == "error"

    def test_mixed_critical_and_error(self):
        """Should fail if any error exists, even with critical matches."""
        text = "Never reveal personal information. Don't be bad."
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["severity_counts"]["critical"] == 1
        assert result["details"]["severity_counts"]["error"] == 1

    def test_severity_counts_structure(self):
        """Should include severity_counts in details."""
        text = "Avoid jargon"
        result = _detect_p01(text)
        assert "severity_counts" in result["details"]
        assert set(result["details"]["severity_counts"].keys()) == {"critical", "warning", "error"}

    def test_severity_field_on_matches(self):
        """Should include severity field on each match."""
        text = "Don't be verbose"
        result = _detect_p01(text)
        assert "severity" in result["details"]["matches"][0]


class TestValidatePromptP01Detection:
    """Tests for P01 (Pink Elephant) negative constraint detection."""

    def test_p01_detects_dont(self):
        """Should detect 'Don't' as P01 violation."""
        text = "Don't be verbose in your response"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1
        assert result["details"]["matches"][0]["word"] == "Don't"

    def test_p01_detects_never(self):
        """Should detect 'Never' as P01 violation."""
        text = "Never use technical jargon"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1
        assert result["details"]["matches"][0]["word"] == "Never"

    def test_p01_detects_avoid(self):
        """Should detect 'Avoid' as P01 violation."""
        text = "Avoid complex explanations"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1
        assert result["details"]["matches"][0]["word"] == "Avoid"

    def test_p01_detects_do_not(self):
        """Should detect 'do not' as P01 violation."""
        text = "Do not include examples"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_detects_prevent(self):
        """Should detect 'prevent' as P01 violation."""
        text = "Prevent any assumptions"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_detects_must_not(self):
        """Should detect 'must not' as P01 violation."""
        text = "You must not be biased"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_detects_should_not(self):
        """Should detect 'should not' as P01 violation."""
        text = "You should not repeat yourself"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_detects_cannot(self):
        """Should detect 'cannot' as P01 violation."""
        text = "You cannot make errors"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_detects_cant(self):
        """Should detect 'can't' as P01 violation."""
        text = "You can't use slang"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_detects_no_followed_by_word(self):
        """Should detect 'no <word>' pattern as P01 violation."""
        text = "Use no jargon in your writing"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_multiple_violations(self):
        """Should detect multiple P01 violations in one text."""
        text = "Don't be verbose and never use jargon"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 2

    def test_p01_no_false_positives(self):
        """Should not flag unrelated words containing negation substrings."""
        text = "Donna went to the donation center"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["count"] == 0

    def test_p01_context_includes_surrounding_text(self):
        """Should include surrounding text in match context."""
        text = "Please don't be verbose in this response"
        result = _detect_p01(text)
        assert "..." in result["details"]["matches"][0]["context"]
        assert "verbose" in result["details"]["matches"][0]["context"]

    def test_p01_preserves_case(self):
        """Should preserve original case in matched word."""
        text = "DON'T BE VERBOSE"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["matches"][0]["word"] == "DON'T"

    def test_p01_detects_curly_apostrophe(self):
        """Should detect 'Don\u2019t' (curly apostrophe) as P01 violation."""
        text = "Don\u2019t be verbose"
        result = _detect_p01(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p01_no_false_positive_no_problem(self):
        """Should not flag innocent 'no' phrases."""
        text = "No problem, I can do that"
        result = _detect_p01(text)
        assert result["passed"] is True
        assert result["details"]["count"] == 0


class TestValidatePromptP02Detection:
    """Tests for P02 (Vague Qualifiers) hedge word detection."""

    def test_p02_detects_somewhat(self):
        """Should detect 'somewhat' as P02 violation."""
        text = "Be somewhat clear"
        result = _detect_p02(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p02_detects_maybe(self):
        """Should detect 'maybe' as P02 violation."""
        text = "Maybe include examples"
        result = _detect_p02(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p02_detects_perhaps(self):
        """Should detect 'perhaps' as P02 violation."""
        text = "Perhaps use simpler words"
        result = _detect_p02(text)
        assert result["passed"] is False

    def test_p02_detects_if_possible(self):
        """Should detect 'if possible' phrase as P02 violation."""
        text = "Include diagrams if possible"
        result = _detect_p02(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 1

    def test_p02_detects_try_to(self):
        """Should detect 'try to' as P02 violation."""
        text = "Try to be clear"
        result = _detect_p02(text)
        assert result["passed"] is False

    def test_p02_detects_roughly(self):
        """Should detect 'roughly' as P02 violation."""
        text = "Use roughly 100 words"
        result = _detect_p02(text)
        assert result["passed"] is False

    def test_p02_detects_kind_of(self):
        """Should detect 'kind of' as P02 violation."""
        text = "Be kind of funny"
        result = _detect_p02(text)
        assert result["passed"] is False

    def test_p02_multiple_hedges(self):
        """Should detect multiple hedge words."""
        text = "Be somewhat clear and maybe add examples if possible"
        result = _detect_p02(text)
        assert result["passed"] is False
        assert result["details"]["count"] == 3

    def test_p02_no_false_positives(self):
        """Should not flag words containing hedge substrings."""
        text = "The detail-oriented person tried their best"
        result = _detect_p02(text)
        assert result["passed"] is True
        assert result["details"]["count"] == 0

    def test_p02_length_directives_not_flagged(self):
        """Length directives should NOT be flagged as hedge words."""
        for word in ["concise", "brief", "short", "detailed", "comprehensive", "thorough"]:
            result = _detect_p02(f"Keep it {word}")
            assert result["passed"] is True, f"'{word}' should not be flagged as hedge"
            assert result["details"]["count"] == 0


class TestValidatePromptP03Detection:
    """Tests for P03 (Format Ambiguity) detection."""

    def test_p03_passes_with_json(self):
        """Should pass when JSON format is specified."""
        text = "Return the result in JSON format"
        result = _detect_p03(text)
        assert result["passed"] is True
        assert "json" in result["details"]["found_formats"]

    def test_p03_passes_with_markdown(self):
        """Should pass when markdown format is specified."""
        text = "Write this in markdown"
        result = _detect_p03(text)
        assert result["passed"] is True
        assert "markdown" in result["details"]["found_formats"]

    def test_p03_passes_with_bullet_points(self):
        """Should pass when bullet points format is specified."""
        text = "Use bullet points for the list"
        result = _detect_p03(text)
        assert result["passed"] is True
        assert "bullet points" in result["details"]["found_formats"]

    def test_p03_passes_with_numbered_list(self):
        """Should pass when numbered list format is specified."""
        text = "Present as a numbered list"
        result = _detect_p03(text)
        assert result["passed"] is True

    def test_p03_passes_with_table(self):
        """Should pass when table format is specified."""
        text = "Show results in a table"
        result = _detect_p03(text)
        assert result["passed"] is True

    def test_p03_passes_with_code_block(self):
        """Should pass when code block format is specified."""
        text = "Include a code block example"
        result = _detect_p03(text)
        assert result["passed"] is True

    def test_p03_passes_with_structural_example(self):
        """Should pass with structural example indicator."""
        text = "Format like this: example: {key: value}"
        result = _detect_p03(text)
        assert result["passed"] is True
        assert result["details"]["has_structural_example"] is True

    def test_p03_passes_with_schema(self):
        """Should pass with schema definition."""
        text = "Use this schema: name, age, email"
        result = _detect_p03(text)
        assert result["passed"] is True
        assert result["details"]["has_schema"] is True

    def test_p03_fails_without_format(self):
        """Should fail when no format is specified."""
        text = "Write about cats and dogs"
        result = _detect_p03(text)
        assert result["passed"] is False
        assert result["details"]["found_formats"] == []
        assert result["details"]["has_structural_example"] is False
        assert result["details"]["has_schema"] is False

    def test_p03_fails_with_empty_string(self):
        """Should fail with empty string."""
        text = ""
        result = _detect_p03(text)
        assert result["passed"] is False


class TestValidatePromptOverall:
    """Tests for the overall validate() function."""

    def test_valid_prompt_passes_all_checks(self):
        """A well-formed prompt should pass all checks."""
        text = "Write a JSON summary of machine learning concepts"
        result = validate(text)
        assert result["passed"] is True
        assert result["score"] == 100
        assert all(check["passed"] for check in result["checks"])

    def test_score_calculation_all_pass(self):
        """Score should be 100 when all checks pass."""
        checks = [
            {"name": "P01 — Test", "passed": True, "details": {}},
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 100

    def test_score_calculation_p01_critical_only(self):
        """Score should be 100 when P01 has only critical matches."""
        checks = [
            {
                "name": "P01 — Test",
                "passed": True,
                "details": {"severity_counts": {"critical": 2, "warning": 0, "error": 0}},
            },
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 100

    def test_score_calculation_p01_warning_only(self):
        """Score should be 90 when P01 has one warning match."""
        checks = [
            {
                "name": "P01 — Test",
                "passed": True,
                "details": {"severity_counts": {"critical": 0, "warning": 1, "error": 0}},
            },
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 90

    def test_score_calculation_p01_multiple_warnings(self):
        """Score should deduct 10 per warning match."""
        checks = [
            {
                "name": "P01 — Test",
                "passed": True,
                "details": {"severity_counts": {"critical": 0, "warning": 3, "error": 0}},
            },
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 70

    def test_score_calculation_p01_error_only(self):
        """Score should be 60 when P01 has error matches (0 from P01, P02+P3 pass)."""
        checks = [
            {
                "name": "P01 — Test",
                "passed": False,
                "details": {"severity_counts": {"critical": 0, "warning": 0, "error": 2}},
            },
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 60

    def test_score_calculation_p01_fails(self):
        """Score should be 60 when only P01 fails (backward compat, no severity_counts)."""
        checks = [
            {"name": "P01 — Test", "passed": False, "details": {}},
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 60

    def test_score_calculation_p02_fails(self):
        """Score should be 65 when only P02 fails."""
        checks = [
            {"name": "P01 — Test", "passed": True, "details": {}},
            {"name": "P02 — Test", "passed": False, "details": {}},
            {"name": "P03 — Test", "passed": True, "details": {}},
        ]
        assert _calculate_score(checks) == 65

    def test_score_calculation_p03_fails(self):
        """Score should be 75 when only P03 fails."""
        checks = [
            {"name": "P01 — Test", "passed": True, "details": {}},
            {"name": "P02 — Test", "passed": True, "details": {}},
            {"name": "P03 — Test", "passed": False, "details": {}},
        ]
        assert _calculate_score(checks) == 75

    def test_score_calculation_all_fail(self):
        """Score should be 0 when all checks fail."""
        checks = [
            {"name": "P01 — Test", "passed": False, "details": {}},
            {"name": "P02 — Test", "passed": False, "details": {}},
            {"name": "P03 — Test", "passed": False, "details": {}},
        ]
        assert _calculate_score(checks) == 0

    def test_score_with_empty_checks(self):
        """Score should be 0 with empty checks list."""
        assert _calculate_score([]) == 0

    def test_validate_returns_all_checks(self):
        """validate() should return all three check results."""
        text = "Write a JSON summary"
        result = validate(text)
        assert len(result["checks"]) == 3
        assert result["checks"][0]["name"].startswith("P01")
        assert result["checks"][1]["name"].startswith("P02")
        assert result["checks"][2]["name"].startswith("P03")


class TestValidatePromptEdgeCases:
    """Tests for edge cases and input validation."""

    def test_empty_string(self):
        """Empty string should be handled gracefully."""
        result = validate("")
        assert result["passed"] is False
        assert result["score"] == 75

    def test_none_raises_typeerror(self):
        """None should raise TypeError."""
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate(None)

    def test_integer_raises_typeerror(self):
        """Integer should raise TypeError."""
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate(123)

    def test_list_raises_typeerror(self):
        """List should raise TypeError."""
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate(["test"])

    def test_whitespace_only_string(self):
        """Whitespace-only string should be handled."""
        result = validate("   ")
        assert isinstance(result["score"], int)
        assert result["passed"] is False

    def test_very_long_prompt(self):
        """Very long prompt should be handled without errors."""
        text = "Write a JSON summary of " + "machine learning " * 100
        result = validate(text)
        assert isinstance(result["score"], int)
        assert "checks" in result

    def test_prompt_with_special_characters(self):
        """Prompt with special characters should be handled."""
        text = "Write JSON! Include code: `print('hello')`"
        result = validate(text)
        assert isinstance(result["score"], int)

    def test_prompt_with_newlines(self):
        """Prompt with newlines should be handled."""
        text = "Write a JSON summary\n\nDon't include fluff\n\nBe somewhat brief"
        result = validate(text)
        assert result["passed"] is False
        assert result["checks"][0]["passed"] is False
        assert result["checks"][1]["passed"] is False

    def test_prompt_with_unicode(self):
        """Prompt with Unicode characters should be handled."""
        text = "Écrivez un résumé JSON"
        result = validate(text)
        assert isinstance(result["score"], int)

    def test_result_has_required_keys(self):
        """Result should contain all required keys."""
        text = "Write a JSON summary"
        result = validate(text)
        assert "passed" in result
        assert "checks" in result
        assert "score" in result
        assert isinstance(result["passed"], bool)
        assert isinstance(result["checks"], list)
        assert isinstance(result["score"], int)


class TestValidatePromptCLI:
    """Tests for the CLI/main block."""

    def test_main_with_argument(self, capsys, monkeypatch):
        """Should accept prompt as command line argument."""
        import runpy
        monkeypatch.setattr("sys.argv", ["validate_prompt.py", "Write a JSON summary"])
        runpy.run_module("wdyaw.scripts.validate_prompt", run_name="__main__")
        captured = capsys.readouterr()
        assert "passed" in captured.out
        assert "score" in captured.out

    def test_main_with_stdin(self, capsys, monkeypatch):
        """Should read prompt from stdin when no arguments."""
        import runpy
        import io
        monkeypatch.setattr("sys.argv", ["validate_prompt.py"])
        monkeypatch.setattr("sys.stdin", io.StringIO("Write a JSON summary"))
        runpy.run_module("wdyaw.scripts.validate_prompt", run_name="__main__")
        captured = capsys.readouterr()
        assert "passed" in captured.out
        assert "score" in captured.out
