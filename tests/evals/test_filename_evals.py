"""Tests for the Alakazam filename evaluation framework and source/author prominence."""

from __future__ import annotations

import shutil
import pytest
from click.testing import CliRunner

from alakazam.cli.main import cli
from alakazam.evals import (
    FilenameEvaluator,
    GOLDEN_DATASET,
    LLMJudgeEvaluator,
)
from alakazam.naming.iso_date import ISODateNaming


class TestGoldenDatasetEvals:
    """Verify all golden dataset cases pass the source/author and quality rubric."""

    @pytest.mark.parametrize("case", GOLDEN_DATASET, ids=[c["id"] for c in GOLDEN_DATASET])
    def test_golden_case_passes_all_eval_checks(self, case):
        evaluator = FilenameEvaluator(max_length=80)
        result = evaluator.evaluate_case(
            case_id=case["id"],
            analysis=case["analysis"],
            original_filename=case["original_filename"],
            expected_sources=case["expected_sources"],
        )

        failed = [f"{c.name}: {c.reason}" for c in result.checks if not c.passed]
        assert result.passed, (
            f"Case {case['id']} produced {result.generated_filename!r} which failed checks: {failed}"
        )
        assert result.score >= 0.95

    @pytest.mark.parametrize(
        "case",
        [c for c in GOLDEN_DATASET if c["id"] != "auto_insurance_claim_notice"],
        ids=[c["id"] for c in GOLDEN_DATASET if c["id"] != "auto_insurance_claim_notice"],
    )
    def test_legacy_bad_filenames_are_caught_by_evaluator(self, case):
        """Verify our evaluator catches the truncation/missing-source bugs from the old pipeline."""
        evaluator = FilenameEvaluator(max_length=80)
        bad_name = case["bad_legacy_filename"]

        result = evaluator.evaluate_case(
            case_id=case["id"],
            analysis=case["analysis"],
            original_filename=case["original_filename"],
            generated_filename=bad_name,
            expected_sources=case["expected_sources"],
        )

        assert not result.passed, (
            f"Expected evaluator to reject legacy bad filename {bad_name!r}, but it passed!"
        )


class TestISODateNamingSourceProminence:
    """Unit tests for source/author extraction and prominence in ISODateNaming."""

    def test_uses_new_filename_when_provided(self):
        naming = ISODateNaming(max_length=80)
        analysis = {
            "document_date": "2026-05-31",
            "new_filename": "2026-05-31 Oak Creek PTA Reimbursement Request Jane Doe.pdf",
            "description": "Payment authorization and reimbursement request form submitted to Oak Creek Elementary PTA by Jane Doe.",
            "metadata": {"organization": "Oak Creek Elementary PTA"},
        }
        result = naming.generate_filename(analysis, "scan.pdf")
        assert result == "2026-05-31 Oak Creek PTA Reimbursement Request Jane Doe.pdf"

    def test_rewrites_prose_description_to_lead_with_source(self):
        naming = ISODateNaming(max_length=80)
        analysis = {
            "document_date": "2026-01-26",
            "description": "Eyewear prescription (Final Spectacle Rx) for John Smith from ClearView Optometry",
            "metadata": {"provider_name": "ClearView Optometry"},
        }
        result = naming.generate_filename(analysis, "scan.pdf")
        assert result.startswith("2026-01-26 Clearview Optometry")
        assert not result.endswith("From.pdf")

    def test_strips_dangling_words_and_commas_on_truncation(self):
        naming = ISODateNaming(max_length=80)
        analysis = {
            "document_date": "2016-08-23",
            "description": "Official academic transcript from the University of Oregon, Springfield for Jane Marie Doe, conferring a Bachelor of Arts in Political Science on August 13, 2010.",
            "metadata": {"provider_name": "University of Oregon, Springfield"},
        }
        result = naming.generate_filename(analysis, "scan.pdf")
        assert result.startswith("2016-08-23 University Of Oregon Springfield")
        assert not result.endswith(",.pdf")
        assert len(result) <= 80


@pytest.mark.asyncio
async def test_llm_judge_evaluator_parses_score(monkeypatch):
    """Test LLMJudgeEvaluator parses JSON score and reasoning from CLI output."""

    class FakeProc:
        returncode = 0

        async def communicate(self):
            return (
                b'{"score": 4.8, "reasoning": "Source is prominently placed right after the date."}',
                b"",
            )

        def kill(self):
            pass

    async def fake_exec(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    judge = LLMJudgeEvaluator(cli_cmd="agy")
    res = await judge.score_filename(
        {"document_date": "2026-01-26", "metadata": {"provider_name": "ClearView Optometry"}},
        "2026-01-26 ClearView Optometry Eyewear Prescription John Smith.pdf",
    )
    assert res["score"] == 4.8
    assert "prominently" in res["reasoning"]


def test_cli_eval_runs_golden_dataset():
    """`alakazam eval` should evaluate the golden dataset and exit 0 when all pass."""
    runner = CliRunner()
    result = runner.invoke(cli, ["eval"])
    assert result.exit_code == 0, result.output
    assert "12/12 passed (100.0%)" in result.output


@pytest.mark.skipif(
    shutil.which("agy") is None,
    reason="Requires Antigravity CLI (agy) for live E2E eval",
)
@pytest.mark.asyncio
async def test_live_llm_judge_on_sample_case():
    """Run live LLM-as-a-Judge via Antigravity CLI on a golden case when agy is installed."""
    case = GOLDEN_DATASET[0]
    naming = ISODateNaming()
    generated = naming.generate_filename(case["analysis"], case["original_filename"])
    judge = LLMJudgeEvaluator(cli_cmd="agy", timeout=90)
    res = await judge.score_filename(case["analysis"], generated)
    assert res["score"] is not None
    assert res["score"] >= 4.0
