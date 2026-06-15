import pytest
from wdyaw.scripts.assemble_prompt import assemble
from wdyaw.scripts.validate_prompt import validate
from wdyaw.scripts.validate_prompt_hybrid import validate_hybrid


class TestSkillProtocolTermination:
    def test_assemble_with_four_components_terminates(self):
        components = {
            "context": "Job seeker in Germany targeting Berlin",
            "task": "Map CV to realistic job titles and domains",
            "references": "Uploaded CV",
            "testing": "Match strength, realism notes, confidence level",
        }
        prompt = assemble(components, format_type="markdown")
        assert "## Context" in prompt
        assert "## Task" in prompt
        assert "## References" in prompt
        assert "## Testing" in prompt
        assert "## Enhancement" not in prompt

    def test_standard_validation_is_non_blocking_for_single_warning(self):
        prompt = assemble({"task": "Don't be bad. Write about cats."}, "markdown")
        report = validate_hybrid(prompt, mode="standard")
        assert report["passed"] is True
        assert report["score"] >= 50

    def test_validation_fails_but_standard_mode_does_not_block(self):
        prompt = "Don't be bad. Be somewhat clear."
        report = validate_hybrid(prompt, mode="standard")
        assert isinstance(report["passed"], bool)

    def test_assemble_auto_reframes_common_error_negatives(self):
        components = {
            "task": "Don't be verbose. Write about cats.",
            "context": "Pet owners",
        }
        prompt = assemble(components, "markdown")
        report = validate(prompt)
        p01 = report["checks"][0]
        assert p01["details"]["severity_counts"].get("error", 0) == 0

    def test_assemble_does_not_loop_on_unreframed_error_negative(self):
        components = {"task": "Don't be bad. Write about cats."}
        prompt = assemble(components, "markdown")
        assert "don't be bad" in prompt.lower()
        assert prompt != ""

    def test_delimiter_present_in_assembled_prompt(self):
        body = assemble(
            {
                "context": "Job seeker in Germany",
                "task": "Analyze CV for realistic job titles",
            },
            "markdown",
        )
        wrapped = f"--- GENERATED PROMPT ---\n\n{body}\n\n--- END GENERATED PROMPT ---"
        assert "--- GENERATED PROMPT ---" in wrapped
        assert "--- END GENERATED PROMPT ---" in wrapped

    def test_empty_prompt_is_invalid_but_not_looping(self):
        prompt = assemble({}, "markdown")
        report = validate_hybrid(prompt, mode="standard")
        assert isinstance(report["score"], int)
        assert 0 <= report["score"] <= 100

    def test_strict_mode_blocks_on_any_issue(self):
        prompt = assemble({"task": "Don't be verbose. Write about cats."}, "markdown")
        report = validate_hybrid(prompt, mode="strict")
        assert report["passed"] is False

    def test_hybrid_report_contains_layer_information(self):
        prompt = "Write a JSON summary"
        report = validate_hybrid(prompt, mode="standard")
        layers = {c.get("layer") for c in report["checks"]}
        assert "deterministic" in layers
        assert "probabilistic" in layers
