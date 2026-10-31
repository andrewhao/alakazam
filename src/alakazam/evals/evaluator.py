"""Deterministic rubric and LLM-as-a-Judge evaluators for generated filenames."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from alakazam.naming.iso_date import ISODateNaming


@dataclass
class EvalCheckResult:
    """Result of an individual rubric check on a filename."""

    name: str
    passed: bool
    score: float
    reason: str


@dataclass
class EvalCaseResult:
    """Evaluation result for a single document test case."""

    case_id: str
    original_filename: str
    generated_filename: str
    expected_sources: List[str]
    passed: bool
    score: float
    checks: List[EvalCheckResult] = field(default_factory=list)
    judge_score: Optional[float] = None
    judge_reasoning: Optional[str] = None


@dataclass
class EvalSuiteResult:
    """Aggregated evaluation results across a dataset or batch."""

    cases: List[EvalCaseResult]

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def failed_count(self) -> int:
        return self.total - self.passed_count

    @property
    def pass_rate(self) -> float:
        return (self.passed_count / self.total) if self.total else 0.0

    @property
    def average_score(self) -> float:
        return (sum(c.score for c in self.cases) / self.total) if self.total else 0.0

    @property
    def average_judge_score(self) -> Optional[float]:
        judged = [c.judge_score for c in self.cases if c.judge_score is not None]
        return (sum(judged) / len(judged)) if judged else None


class FilenameEvaluator:
    """
    Evaluates generated filenames against Alakazam's quality rubric:
    1. Valid ISO date format and length (<= max_length)
    2. Document source / author is present in the filename
    3. Document source / author is prominently placed near the beginning (after date)
    4. No dangling prepositions, articles, conjunctions, or punctuation from truncation
    5. Concise title style rather than a raw prose sentence
    """

    PROSE_FILLER_WORDS = {
        "conferring",
        "covering",
        "including",
        "regarding",
        "reporting",
        "requiring",
        "showing",
        "submitted",
        "totaling",
    }

    def __init__(self, max_length: int = 80):
        self.max_length = max_length
        self.naming = ISODateNaming(max_length=max_length)

    def evaluate_case(
        self,
        case_id: str,
        analysis: Dict,
        original_filename: str = "document.pdf",
        generated_filename: Optional[str] = None,
        expected_sources: Optional[Sequence[str]] = None,
    ) -> EvalCaseResult:
        """Evaluate a filename (or generate one via ISODateNaming and evaluate it)."""
        filename = generated_filename or self.naming.generate_filename(analysis, original_filename)

        sources = list(expected_sources or [])
        if not sources:
            extracted = ISODateNaming.extract_source(analysis, original_name=original_filename)
            if extracted:
                sources = ISODateNaming._source_match_candidates(extracted)

        checks = [
            self.check_format(filename),
            self.check_source_presence(filename, sources, analysis),
            self.check_source_prominence(filename, sources, analysis),
            self.check_no_dangling_truncation(filename),
            self.check_not_prose_sentence(filename),
        ]

        passed = all(c.passed for c in checks)
        score = sum(c.score for c in checks) / len(checks) if checks else 0.0

        return EvalCaseResult(
            case_id=case_id,
            original_filename=original_filename,
            generated_filename=filename,
            expected_sources=sources,
            passed=passed,
            score=score,
            checks=checks,
        )

    def check_format(self, filename: str) -> EvalCheckResult:
        """Verify YYYY-MM-DD prefix, valid characters, extension, and length <= max_length."""
        if not self.naming.validate(filename):
            return EvalCheckResult(
                name="format_valid",
                passed=False,
                score=0.0,
                reason=f"Filename {filename!r} does not match 'YYYY-MM-DD <Name>.<ext>'",
            )
        if len(filename) > self.max_length:
            return EvalCheckResult(
                name="format_valid",
                passed=False,
                score=0.0,
                reason=f"Filename length ({len(filename)}) exceeds max_length ({self.max_length})",
            )
        return EvalCheckResult(
            name="format_valid",
            passed=True,
            score=1.0,
            reason=f"Valid format and length ({len(filename)}/{self.max_length} chars)",
        )

    def check_source_presence(
        self,
        filename: str,
        expected_sources: Sequence[str],
        analysis: Optional[Dict] = None,
    ) -> EvalCheckResult:
        """Verify the document source or author appears in the filename."""
        candidates = self._expand_source_candidates(expected_sources, analysis)
        if not candidates:
            return EvalCheckResult(
                name="source_present",
                passed=False,
                score=0.0,
                reason="No document source/author could be identified in metadata or ground truth",
            )

        stem = ISODateNaming._extract_stem_from_filename(filename)
        stem_norm = self._normalize_for_match(stem)

        # Reject placeholder "unknown" source strings in the filename
        for bad_src in ISODateNaming.UNKNOWN_SOURCE_VALUES:
            if bad_src.startswith("unknown") and bad_src in stem_norm:
                return EvalCheckResult(
                    name="source_present",
                    passed=False,
                    score=0.0,
                    reason=f"Filename contains placeholder source {bad_src!r}",
                )

        for cand in candidates:
            cand_norm = self._normalize_for_match(cand)
            if cand_norm and cand_norm in stem_norm:
                return EvalCheckResult(
                    name="source_present",
                    passed=True,
                    score=1.0,
                    reason=f"Found source/author {cand!r} in filename",
                )

        return EvalCheckResult(
            name="source_present",
            passed=False,
            score=0.0,
            reason=f"Missing source/author (expected one of {list(expected_sources)!r}) in {filename!r}",
        )

    def check_source_prominence(
        self,
        filename: str,
        expected_sources: Sequence[str],
        analysis: Optional[Dict] = None,
    ) -> EvalCheckResult:
        """Verify the document source/author appears near the front of the filename after the date."""
        candidates = self._expand_source_candidates(expected_sources, analysis)
        if not candidates:
            return EvalCheckResult(
                name="source_prominent",
                passed=False,
                score=0.0,
                reason="No source/author candidates available to check prominence",
            )

        stem = ISODateNaming._extract_stem_from_filename(filename)
        stem_norm = self._normalize_for_match(stem)

        # Reject placeholder "unknown" source strings in the filename
        for bad_src in ISODateNaming.UNKNOWN_SOURCE_VALUES:
            if bad_src.startswith("unknown") and bad_src in stem_norm:
                return EvalCheckResult(
                    name="source_present",
                    passed=False,
                    score=0.0,
                    reason=f"Filename contains placeholder source {bad_src!r}",
                )

        best_idx: Optional[int] = None
        matched_cand: Optional[str] = None
        for cand in candidates:
            cand_norm = self._normalize_for_match(cand)
            if not cand_norm:
                continue
            idx = stem_norm.find(cand_norm)
            if idx != -1 and (best_idx is None or idx < best_idx):
                best_idx = idx
                matched_cand = cand

        if best_idx is None:
            return EvalCheckResult(
                name="source_prominent",
                passed=False,
                score=0.0,
                reason="Source/author not found in filename stem",
            )

        # Prominent if it starts at index 0 (immediately after date) or within first 10 chars (not preceded by "from ")
        if best_idx == 0:
            return EvalCheckResult(
                name="source_prominent",
                passed=True,
                score=1.0,
                reason=f"Source/author {matched_cand!r} leads immediately after the date",
            )
        prefix = stem_norm[:best_idx].strip()
        if best_idx <= 10 and not prefix.endswith("from"):
            return EvalCheckResult(
                name="source_prominent",
                passed=True,
                score=0.9,
                reason=f"Source/author {matched_cand!r} appears near start (offset {best_idx})",
            )

        return EvalCheckResult(
            name="source_prominent",
            passed=False,
            score=0.25,
            reason=f"Source/author {matched_cand!r} does not lead the filename (offset {best_idx})",
        )

    def check_no_dangling_truncation(self, filename: str) -> EvalCheckResult:
        """Verify the filename does not end with a dangling preposition, article, single initial, or comma."""
        stem = ISODateNaming._extract_stem_from_filename(filename)
        words = stem.split()
        if not words:
            return EvalCheckResult(
                name="no_dangling_truncation",
                passed=False,
                score=0.0,
                reason="Filename has an empty descriptive stem",
            )

        last_token = words[-1]
        if last_token[-1] in ",;:-([":
            return EvalCheckResult(
                name="no_dangling_truncation",
                passed=False,
                score=0.0,
                reason=f"Filename stem ends with dangling punctuation: {last_token!r}",
            )

        last_word_clean = last_token.strip(".,;:-()[]{}").lower()
        if last_word_clean in ISODateNaming.DANGLING_WORDS:
            return EvalCheckResult(
                name="no_dangling_truncation",
                passed=False,
                score=0.0,
                reason=f"Filename stem ends with dangling word {last_token!r}",
            )

        if len(last_word_clean) == 1 and last_word_clean.isalpha():
            return EvalCheckResult(
                name="no_dangling_truncation",
                passed=False,
                score=0.0,
                reason=f"Filename stem ends with truncated single-letter initial {last_token!r}",
            )

        return EvalCheckResult(
            name="no_dangling_truncation",
            passed=True,
            score=1.0,
            reason="Clean ending word boundary",
        )

    def check_not_prose_sentence(self, filename: str) -> EvalCheckResult:
        """Verify the filename is a concise title and not a verbose prose sentence."""
        stem = ISODateNaming._extract_stem_from_filename(filename)
        words_lower = [w.strip(".,;:-()[]{}").lower() for w in stem.split()]

        found_filler = [w for w in words_lower if w in self.PROSE_FILLER_WORDS]
        if found_filler:
            return EvalCheckResult(
                name="concise_title",
                passed=False,
                score=0.0,
                reason=f"Filename contains prose filler words: {found_filler}",
            )

        return EvalCheckResult(
            name="concise_title",
            passed=True,
            score=1.0,
            reason="Filename uses concise title style",
        )

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text).lower()
        return re.sub(r"\s{2,}", " ", cleaned).strip()

    @staticmethod
    def _expand_source_candidates(
        expected_sources: Sequence[str],
        analysis: Optional[Dict] = None,
    ) -> List[str]:
        candidates: List[str] = []
        for src in expected_sources:
            if src and src.strip():
                candidates.append(src.strip())
                candidates.extend(ISODateNaming._source_match_candidates(src.strip()))

        if analysis:
            extracted = ISODateNaming.extract_source(analysis)
            if extracted:
                candidates.append(extracted)
                candidates.extend(ISODateNaming._source_match_candidates(extracted))

        return list(dict.fromkeys(candidates))


class LLMJudgeEvaluator:
    """
    LLM-as-a-Judge evaluator that shells out to an AI CLI (`agy`, `claude`, or `codex`)
    to grade a generated filename from 1.0 to 5.0 on source prominence and naming quality.
    """

    def __init__(self, cli_cmd: str = "agy", timeout: int = 60):
        self.cli_cmd = cli_cmd
        self.timeout = timeout

    async def score_filename(
        self,
        analysis: Dict,
        generated_filename: str,
    ) -> Dict[str, object]:
        """
        Ask the LLM judge to evaluate generated_filename given the document analysis.

        Returns:
            {"score": float (1.0-5.0), "reasoning": str}
        """
        prompt = f"""You are an evaluation judge for a document renaming system.
Grade the following generated PDF filename on a scale from 1 to 5 based on these strict criteria:
1. **Source / Author Prominence (most important)**: Does the filename clearly highlight the issuing organization, company, institution, or author right near the beginning after the YYYY-MM-DD date?
2. **Conciseness & No Truncation Artifacts**: Is it a clean, readable title under 80 characters without mid-sentence truncation or dangling prepositions (e.g., "From.pdf", "Submitted.pdf", "California,.pdf")?
3. **Key Identifiers**: Does it include the document type and key subject/recipient?

Document Analysis Metadata:
{json.dumps(analysis, indent=2, ensure_ascii=False)}

Generated Filename:
{generated_filename}

Respond ONLY with valid JSON in this exact format:
{{
  "score": 5,
  "reasoning": "One sentence explanation of the score."
}}"""

        if self.cli_cmd == "agy":
            cmd = [
                "agy",
                "--dangerously-skip-permissions",
                "--output-format",
                "text",
                "-p",
                prompt,
            ]
        elif self.cli_cmd == "codex":
            cmd = ["codex", "exec", prompt]
        else:
            cmd = ["claude", "-p", prompt, "--output-format", "text"]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return {"score": None, "reasoning": "LLM judge timed out"}

        text = stdout.decode("utf-8", errors="replace").strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {"score": None, "reasoning": f"Could not parse judge output: {text[:120]}"}

        try:
            parsed = json.loads(match.group(0))
            return {
                "score": float(parsed.get("score", 0.0)),
                "reasoning": str(parsed.get("reasoning", "")),
            }
        except Exception as e:
            return {"score": None, "reasoning": f"Invalid JSON from judge: {e}"}
