import pytest
from wdyaw.scripts.validate_prompt_llm import (
    validate_llm,
)
from wdyaw.scripts.validate_prompt_hybrid import (
    validate_hybrid,
    _deduplicate_findings,
    _calculate_hybrid_score,
    _count_deduplicated,
)


class TestValidatePromptLLM:
    """Tests for the probabilistic validation layer (validate_prompt_llm.py)."""

    def test_detects_semantic_negation_refrain_from(self):
        text = "Please refrain from using complex terms"
        result = validate_llm(text)
        p04 = result["checks"][0]
        assert p04["name"] == "P04 — Semantic Negation (Indirect Negatives)"
        assert p04["passed"] is False
        assert p04["details"]["count"] == 1
        assert "refrain" in p04["details"]["matches"][0]["word"].lower()

    def test_detects_semantic_negation_steer_clear(self):
        text = "Steer clear of technical jargon"
        result = validate_llm(text)
        p04 = result["checks"][0]
        assert p04["passed"] is False
        assert "steer clear" in p04["details"]["matches"][0]["word"].lower()

    def test_detects_semantic_negation_eschew(self):
        text = "Eschew verbose explanations"
        result = validate_llm(text)
        p04 = result["checks"][0]
        assert p04["passed"] is False
        assert p04["details"]["matches"][0]["word"].lower() == "eschew"

    def test_detects_implied_negative_keep_it_simple(self):
        text = "Keep it simple and straightforward"
        result = validate_llm(text)
        p05 = result["checks"][1]
        assert p05["name"] == "P05 — Implied Negative Constraints"
        assert p05["passed"] is False
        assert "keep it simple" in p05["details"]["matches"][0]["word"].lower()

    def test_detects_implied_negative_use_plain_english(self):
        text = "Use plain English in your response"
        result = validate_llm(text)
        p05 = result["checks"][1]
        assert p05["passed"] is False
        assert "use plain english" in p05["details"]["matches"][0]["word"].lower()

    def test_detects_contextual_hedge_relatively(self):
        text = "Use relatively simple language"
        result = validate_llm(text)
        p06 = result["checks"][2]
        assert p06["name"] == "P06 — Contextual Hedge Words"
        assert p06["passed"] is False
        assert "relatively" in p06["details"]["matches"][0]["word"].lower()

    def test_detects_contextual_hedge_fairly(self):
        text = "Keep it fairly brief"
        result = validate_llm(text)
        p06 = result["checks"][2]
        assert p06["passed"] is False
        assert "fairly" in p06["details"]["matches"][0]["word"].lower()

    def test_clean_prompt_passes_all(self):
        text = "Write a JSON summary of machine learning concepts"
        result = validate_llm(text)
        assert result["passed"] is True
        assert result["score"] == 100
        assert all(check["passed"] for check in result["checks"])

    def test_empty_string(self):
        result = validate_llm("")
        assert result["passed"] is True
        assert result["score"] == 100

    def test_none_raises_typeerror(self):
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate_llm(None)

    def test_integer_raises_typeerror(self):
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate_llm(123)

    def test_unicode_prompt(self):
        text = "Écrivez un résumé JSON"
        result = validate_llm(text)
        assert isinstance(result["score"], int)
        assert result["passed"] is True

    def test_very_long_prompt(self):
        text = "Write a JSON summary of " + "machine learning " * 100
        result = validate_llm(text)
        assert isinstance(result["score"], int)
        assert "checks" in result

    def test_llm_fn_provided_valid_json(self):
        def mock_llm(prompt: str) -> str:
            return """{
                "findings": [
                    {
                        "category": "semantic_negation",
                        "severity": "error",
                        "text": "refrain from using",
                        "position": 10,
                        "suggestion": "Use simple language"
                    }
                ],
                "semantic_negation_count": 1,
                "implied_negative_count": 0,
                "contextual_hedge_count": 0
            }"""

        result = validate_llm("Please refrain from using jargon", llm_fn=mock_llm)
        assert result["passed"] is True  # Non-blocking: score = 70 >= 50
        assert result["checks"][0]["details"]["count"] == 1
        assert result["checks"][0]["details"]["matches"][0]["suggestion"] == "Use simple language"

    def test_llm_fn_provided_json_with_code_block(self):
        def mock_llm(prompt: str) -> str:
            return """```json
            {
                "findings": [],
                "semantic_negation_count": 0,
                "implied_negative_count": 0,
                "contextual_hedge_count": 0
            }
            ```"""

        result = validate_llm("Write a JSON summary", llm_fn=mock_llm)
        assert result["passed"] is True
        assert result["score"] == 100

    def test_llm_fn_returns_invalid_json_fallback(self):
        def mock_llm(prompt: str) -> str:
            return "not valid json"

        result = validate_llm("Please refrain from using jargon", llm_fn=mock_llm)
        p04 = result["checks"][0]
        assert p04["passed"] is False
        assert p04["details"]["count"] == 1

    def test_llm_fn_returns_none_fallback(self):
        def mock_llm(prompt):
            return None

        result = validate_llm("Please refrain from using jargon", llm_fn=mock_llm)
        p04 = result["checks"][0]
        assert p04["passed"] is False

    def test_llm_fn_returns_empty_string_fallback(self):
        def mock_llm(prompt: str) -> str:
            return ""

        result = validate_llm("Please refrain from using jargon", llm_fn=mock_llm)
        p04 = result["checks"][0]
        assert p04["passed"] is False

    def test_result_structure(self):
        text = "Keep it simple"
        result = validate_llm(text)
        assert "passed" in result
        assert "checks" in result
        assert "score" in result
        assert len(result["checks"]) == 3
        assert result["checks"][0]["name"].startswith("P04")
        assert result["checks"][1]["name"].startswith("P05")
        assert result["checks"][2]["name"].startswith("P06")

    def test_semantic_match_includes_context(self):
        text = "Please refrain from using complex terms"
        result = validate_llm(text)
        match = result["checks"][0]["details"]["matches"][0]
        assert "context" in match
        assert "..." in match["context"]

    def test_multiple_semantic_issues(self):
        text = "Refrain from jargon. Keep it simple. Use relatively plain English."
        result = validate_llm(text)
        assert result["checks"][0]["details"]["count"] >= 1
        assert result["checks"][1]["details"]["count"] >= 1
        assert result["checks"][2]["details"]["count"] >= 1
        assert result["score"] < 100

    def test_no_false_positives_on_common_words(self):
        text = "Please refer to the document. Stay at the hotel."
        result = validate_llm(text)
        assert result["passed"] is True
        assert result["score"] == 100

    def test_score_with_all_probabilistic_fails(self):
        text = "Refrain from jargon. Keep it simple. Use relatively plain English."
        result = validate_llm(text)
        assert result["score"] == 0
        assert result["passed"] is False

    def test_score_with_one_warning(self):
        text = "Keep it simple"
        result = validate_llm(text)
        assert result["checks"][1]["passed"] is False
        assert result["checks"][0]["passed"] is True
        assert result["checks"][2]["passed"] is True
        assert result["score"] == 65


class TestValidatePromptHybrid:
    """Tests for the hybrid validation orchestrator (validate_prompt_hybrid.py)."""

    def test_fast_mode_passes_clean_prompt(self):
        text = "Write a JSON summary of machine learning"
        result = validate_hybrid(text, mode="fast")
        assert result["passed"] is True
        assert result["mode"] == "fast"
        assert result["probabilistic"] is None
        assert len(result["checks"]) == 3
        assert all(c.get("layer") == "deterministic" for c in result["checks"])

    def test_fast_mode_non_blocking(self):
        text = "Write a JSON summary. Don't be verbose."
        result = validate_hybrid(text, mode="fast")
        assert result["mode"] == "fast"
        assert result["score"] >= 50
        assert result["passed"] is True

    def test_fast_mode_blocks_on_catastrophic(self):
        text = "Don't be verbose. Be somewhat clear."
        result = validate_hybrid(text, mode="fast")
        assert result["score"] < 50
        assert result["passed"] is False

    def test_standard_mode_runs_both_layers(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text, mode="standard")
        assert result["mode"] == "standard"
        assert result["probabilistic"] is not None
        assert len(result["checks"]) == 6
        det_count = sum(1 for c in result["checks"] if c.get("layer") == "deterministic")
        prob_count = sum(1 for c in result["checks"] if c.get("layer") == "probabilistic")
        assert det_count == 3
        assert prob_count == 3

    def test_standard_mode_non_blocking(self):
        text = "Don't be verbose"
        result = validate_hybrid(text, mode="standard")
        assert result["passed"] is True
        assert result["score"] >= 50

    def test_strict_mode_blocks_on_any_issue(self):
        text = "Don't be verbose"
        result = validate_hybrid(text, mode="strict")
        assert result["passed"] is False
        assert result["mode"] == "strict"

    def test_strict_mode_passes_clean_prompt(self):
        text = "Write a JSON summary of machine learning concepts"
        result = validate_hybrid(text, mode="strict")
        assert result["passed"] is True

    def test_invalid_mode_raises_valueerror(self):
        with pytest.raises(ValueError, match="mode must be one of"):
            validate_hybrid("test", mode="invalid")

    def test_none_prompt_raises_typeerror(self):
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate_hybrid(None)

    def test_integer_prompt_raises_typeerror(self):
        with pytest.raises(TypeError, match="prompt_text must be str"):
            validate_hybrid(123)

    def test_empty_string_fast(self):
        result = validate_hybrid("", mode="fast")
        assert result["passed"] is True
        assert result["score"] == 75

    def test_empty_string_standard(self):
        result = validate_hybrid("", mode="standard")
        assert result["passed"] is True

    def test_empty_string_strict(self):
        result = validate_hybrid("", mode="strict")
        assert result["passed"] is False

    def test_whitespace_only_fast(self):
        result = validate_hybrid("   ", mode="fast")
        assert result["passed"] is True

    def test_unicode_prompt(self):
        text = "Écrivez un résumé JSON"
        result = validate_hybrid(text, mode="standard")
        assert isinstance(result["score"], int)
        assert result["passed"] is True

    def test_very_long_prompt(self):
        text = "Write a JSON summary of " + "machine learning " * 100
        result = validate_hybrid(text, mode="standard")
        assert isinstance(result["score"], int)
        assert "checks" in result

    def test_hybrid_score_calculation(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text, mode="standard")
        assert 0 <= result["score"] <= 100
        assert result["score"] > result["deterministic"]["score"] - 20

    def test_deduplicated_count_clean_prompt(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text, mode="standard")
        assert result["deduplicated_count"] == 0

    def test_deduplicated_count_with_issues(self):
        text = "Don't be verbose. Refrain from jargon."
        result = validate_hybrid(text, mode="standard")
        assert result["deduplicated_count"] >= 2

    def test_result_has_required_keys(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text, mode="standard")
        assert "passed" in result
        assert "mode" in result
        assert "checks" in result
        assert "score" in result
        assert "deterministic" in result
        assert "probabilistic" in result
        assert "deduplicated_count" in result

    def test_deterministic_sub_report_preserved(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text, mode="standard")
        det = result["deterministic"]
        assert "passed" in det
        assert "checks" in det
        assert "score" in det
        assert len(det["checks"]) == 3

    def test_probabilistic_sub_report_preserved(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text, mode="standard")
        prob = result["probabilistic"]
        assert prob is not None
        assert "passed" in prob
        assert "checks" in prob
        assert "score" in prob
        assert len(prob["checks"]) == 3

    def test_fast_mode_uses_deterministic_only(self):
        text = "Refrain from using jargon"
        result = validate_hybrid(text, mode="fast")
        assert result["passed"] is True
        assert result["probabilistic"] is None

    def test_standard_mode_catches_semantic_issues(self):
        text = "Refrain from using jargon"
        result = validate_hybrid(text, mode="standard")
        prob_checks = [c for c in result["checks"] if c.get("layer") == "probabilistic"]
        p04 = prob_checks[0]
        assert p04["passed"] is False
        assert p04["details"]["count"] >= 1

    def test_strict_mode_with_both_layers_fails(self):
        text = "Don't be verbose. Refrain from jargon."
        result = validate_hybrid(text, mode="strict")
        assert result["passed"] is False

    def test_llm_fn_passed_to_probabilistic_layer(self):
        def mock_llm(prompt: str) -> str:
            return """{
                "findings": [
                    {
                        "category": "semantic_negation",
                        "severity": "error",
                        "text": "refrain from",
                        "position": 0,
                        "suggestion": "Use simple terms"
                    }
                ],
                "semantic_negation_count": 1,
                "implied_negative_count": 0,
                "contextual_hedge_count": 0
            }"""

        text = "Refrain from using jargon"
        result = validate_hybrid(text, mode="standard", llm_fn=mock_llm)
        prob = result["probabilistic"]
        assert prob["checks"][0]["details"]["count"] == 1
        assert prob["checks"][0]["details"]["matches"][0]["suggestion"] == "Use simple terms"

    def test_default_mode_is_fast(self):
        text = "Write a JSON summary"
        result = validate_hybrid(text)
        assert result["mode"] == "fast"


class TestHybridDeduplication:
    """Tests for the _deduplicate_findings helper."""

    def test_no_duplicates_keeps_all(self):
        det = [
            {
                "name": "P01 — Test",
                "passed": False,
                "details": {
                    "count": 1,
                    "matches": [{"word": "don't", "position": 0}],
                },
            }
        ]
        prob = [
            {
                "name": "P04 — Test",
                "passed": False,
                "details": {
                    "count": 1,
                    "matches": [{"word": "refrain", "position": 10}],
                },
            }
        ]
        merged = _deduplicate_findings(det, prob)
        assert len(merged) == 2
        assert merged[0]["details"]["count"] == 1
        assert merged[1]["details"]["count"] == 1

    def test_removes_exact_duplicates(self):
        det = [
            {
                "name": "P01 — Test",
                "passed": False,
                "details": {
                    "count": 1,
                    "matches": [{"word": "don't", "position": 5}],
                },
            }
        ]
        prob = [
            {
                "name": "P04 — Test",
                "passed": False,
                "details": {
                    "count": 1,
                    "matches": [{"word": "don't", "position": 5}],
                },
            }
        ]
        merged = _deduplicate_findings(det, prob)
        assert len(merged) == 2
        assert merged[0]["details"]["count"] == 1
        assert merged[1]["details"]["count"] == 0

    def test_case_insensitive_dedup(self):
        det = [
            {
                "name": "P01 — Test",
                "passed": False,
                "details": {
                    "count": 1,
                    "matches": [{"word": "Don't", "position": 5}],
                },
            }
        ]
        prob = [
            {
                "name": "P04 — Test",
                "passed": False,
                "details": {
                    "count": 1,
                    "matches": [{"word": "don't", "position": 5}],
                },
            }
        ]
        merged = _deduplicate_findings(det, prob)
        assert merged[0]["details"]["count"] == 1
        assert merged[1]["details"]["count"] == 0

    def test_preserves_layer_info(self):
        det = [
            {
                "name": "P01 — Test",
                "passed": True,
                "details": {"count": 0, "matches": []},
            }
        ]
        prob = [
            {
                "name": "P04 — Test",
                "passed": True,
                "details": {"count": 0, "matches": []},
            }
        ]
        merged = _deduplicate_findings(det, prob)
        assert merged[0]["layer"] == "deterministic"
        assert merged[1]["layer"] == "probabilistic"


class TestHybridScoreCalculation:
    """Tests for the _calculate_hybrid_score helper."""

    def test_all_passed_score_100(self):
        checks = [
            {"name": "P01 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P02 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P03 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P04 — Test", "passed": True, "layer": "probabilistic"},
            {"name": "P05 — Test", "passed": True, "layer": "probabilistic"},
            {"name": "P06 — Test", "passed": True, "layer": "probabilistic"},
        ]
        assert _calculate_hybrid_score(checks) == 100

    def test_all_failed_score_0(self):
        checks = [
            {"name": "P01 — Test", "passed": False, "layer": "deterministic"},
            {"name": "P02 — Test", "passed": False, "layer": "deterministic"},
            {"name": "P03 — Test", "passed": False, "layer": "deterministic"},
            {"name": "P04 — Test", "passed": False, "layer": "probabilistic"},
            {"name": "P05 — Test", "passed": False, "layer": "probabilistic"},
            {"name": "P06 — Test", "passed": False, "layer": "probabilistic"},
        ]
        assert _calculate_hybrid_score(checks) == 0

    def test_one_deterministic_fail(self):
        checks = [
            {"name": "P01 — Test", "passed": False, "layer": "deterministic"},
            {"name": "P02 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P03 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P04 — Test", "passed": True, "layer": "probabilistic"},
            {"name": "P05 — Test", "passed": True, "layer": "probabilistic"},
            {"name": "P06 — Test", "passed": True, "layer": "probabilistic"},
        ]
        assert _calculate_hybrid_score(checks) == 76

    def test_one_probabilistic_fail(self):
        checks = [
            {"name": "P01 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P02 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P03 — Test", "passed": True, "layer": "deterministic"},
            {"name": "P04 — Test", "passed": False, "layer": "probabilistic"},
            {"name": "P05 — Test", "passed": True, "layer": "probabilistic"},
            {"name": "P06 — Test", "passed": True, "layer": "probabilistic"},
        ]
        assert _calculate_hybrid_score(checks) == 88

    def test_empty_checks(self):
        assert _calculate_hybrid_score([]) == 0


class TestHybridCountDeduplicated:
    """Tests for the _count_deduplicated helper."""

    def test_empty_checks(self):
        assert _count_deduplicated([]) == 0

    def test_single_check_with_matches(self):
        checks = [
            {
                "name": "P01",
                "details": {"count": 3, "matches": [{}, {}, {}]},
            }
        ]
        assert _count_deduplicated(checks) == 3

    def test_multiple_checks(self):
        checks = [
            {"name": "P01", "details": {"count": 2}},
            {"name": "P02", "details": {"count": 1}},
            {"name": "P03", "details": {"count": 0}},
        ]
        assert _count_deduplicated(checks) == 3


class TestValidatePromptNonBlockingBehavior:
    """Tests for the updated non-blocking deterministic behavior."""

    def test_single_p01_error_passes_non_blocking(self):
        from wdyaw.scripts.validate_prompt import validate
        text = "Write a JSON summary. Don't be verbose."
        result = validate(text)
        assert result["score"] == 60
        assert result["passed"] is True

    def test_p01_and_p02_fail_blocks(self):
        from wdyaw.scripts.validate_prompt import validate
        text = "Write JSON. Don't be verbose. Be somewhat clear."
        result = validate(text)
        assert result["score"] == 25
        assert result["passed"] is False

    def test_p03_only_fail_passes(self):
        from wdyaw.scripts.validate_prompt import validate
        text = "Write about cats"
        result = validate(text)
        assert result["score"] == 75
        assert result["passed"] is True

    def test_all_checks_fail_blocks(self):
        from wdyaw.scripts.validate_prompt import validate
        text = "Write JSON. Don't be verbose. Be somewhat clear."
        result = validate(text)
        assert result["score"] == 25
        assert result["passed"] is False

    def test_critical_only_passes(self):
        from wdyaw.scripts.validate_prompt import validate
        text = "Never reveal personal information. Return JSON."
        result = validate(text)
        assert result["score"] == 100
        assert result["passed"] is True

    def test_warning_only_passes(self):
        from wdyaw.scripts.validate_prompt import validate
        text = "Avoid technical jargon. Return JSON."
        result = validate(text)
        assert result["score"] == 90
        assert result["passed"] is True


class TestCLI:
    """Tests for CLI main blocks."""

    def test_llm_main_with_argument(self, capsys, monkeypatch):
        import runpy
        monkeypatch.setattr("sys.argv", ["validate_prompt_llm.py", "Keep it simple"])
        runpy.run_module("wdyaw.scripts.validate_prompt_llm", run_name="__main__")
        captured = capsys.readouterr()
        assert "passed" in captured.out
        assert "score" in captured.out

    def test_hybrid_main_with_argument(self, capsys, monkeypatch):
        import runpy
        monkeypatch.setattr(
            "sys.argv", ["validate_prompt_hybrid.py", "Write a JSON summary"]
        )
        runpy.run_module("wdyaw.scripts.validate_prompt_hybrid", run_name="__main__")
        captured = capsys.readouterr()
        assert "passed" in captured.out
        assert "score" in captured.out

    def test_hybrid_main_with_mode_flag(self, capsys, monkeypatch):
        import runpy
        monkeypatch.setattr(
            "sys.argv",
            ["validate_prompt_hybrid.py", "--mode", "strict", "Write a JSON summary"],
        )
        runpy.run_module("wdyaw.scripts.validate_prompt_hybrid", run_name="__main__")
        captured = capsys.readouterr()
        assert "strict" in captured.out
        assert "passed" in captured.out
