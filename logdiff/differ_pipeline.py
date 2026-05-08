"""Pipeline orchestrator that chains diff, filter, score, annotate, and tag steps."""

from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff, diff_entries
from logdiff.filter import filter_by_fields, filter_by_status
from logdiff.scorer import ScoredDiff, score_diffs
from logdiff.annotator import AnnotatedDiff, annotate_diffs
from logdiff.tagger import TaggedDiff, tag_diffs
from logdiff.reporter import DiffReport, build_report


class PipelineError(Exception):
    """Raised when the pipeline is misconfigured or fails."""


@dataclass
class PipelineConfig:
    include_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    status_filter: Optional[str] = None
    min_score: float = 0.0
    annotate: bool = True
    tag: bool = True
    custom_rules: Optional[dict] = None
    custom_tags: Optional[dict] = None


@dataclass
class PipelineResult:
    diffs: List[EntryDiff]
    scored: List[ScoredDiff]
    annotated: List[AnnotatedDiff]
    tagged: List[TaggedDiff]
    report: DiffReport

    @property
    def total(self) -> int:
        return len(self.diffs)

    @property
    def changed(self) -> int:
        return sum(1 for d in self.diffs if d.has_changes())


def run_pipeline(
    before: List[dict],
    after: List[dict],
    key: str = "id",
    config: Optional[PipelineConfig] = None,
) -> PipelineResult:
    """Run the full logdiff pipeline and return a structured result."""
    if config is None:
        config = PipelineConfig()

    diffs: List[EntryDiff] = diff_entries(before, after, key=key)

    if config.include_fields or config.exclude_fields:
        diffs = filter_by_fields(
            diffs,
            include=config.include_fields,
            exclude=config.exclude_fields,
        )

    if config.status_filter:
        diffs = filter_by_status(diffs, status=config.status_filter)

    scored = score_diffs(diffs)

    if config.min_score > 0.0:
        scored = [s for s in scored if s.score >= config.min_score]
        scored_keys = {id(s.diff) for s in scored}
        diffs = [d for d in diffs if id(d) in scored_keys]

    annotated: List[AnnotatedDiff] = []
    if config.annotate:
        annotated = annotate_diffs(diffs, custom_rules=config.custom_rules or {})

    tagged: List[TaggedDiff] = []
    if config.tag:
        tagged = tag_diffs(diffs, custom_tags=config.custom_tags or {})

    report = build_report(diffs)

    return PipelineResult(
        diffs=diffs,
        scored=scored,
        annotated=annotated,
        tagged=tagged,
        report=report,
    )
