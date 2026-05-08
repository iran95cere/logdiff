"""Tests for the differ_pipeline orchestration module."""

import pytest
from logdiff.differ_pipeline import PipelineConfig, PipelineResult, run_pipeline, PipelineError


BEFORE = [
    {"id": "a", "status": "ok", "latency": 120, "region": "us-east"},
    {"id": "b", "status": "ok", "latency": 80,  "region": "eu-west"},
    {"id": "c", "status": "ok", "latency": 200, "region": "us-west"},
]

AFTER = [
    {"id": "a", "status": "degraded", "latency": 450, "region": "us-east"},
    {"id": "b", "status": "ok",       "latency": 80,  "region": "eu-west"},
    {"id": "d", "status": "ok",       "latency": 55,  "region": "ap-south"},
]


def test_run_pipeline_returns_pipeline_result():
    result = run_pipeline(BEFORE, AFTER)
    assert isinstance(result, PipelineResult)


def test_run_pipeline_total_counts_all_diffs():
    result = run_pipeline(BEFORE, AFTER)
    # a modified, b unchanged, c removed, d added => 4 diffs
    assert result.total == 4


def test_run_pipeline_changed_excludes_unchanged():
    result = run_pipeline(BEFORE, AFTER)
    # b is unchanged
    assert result.changed == 3


def test_run_pipeline_report_is_populated():
    result = run_pipeline(BEFORE, AFTER)
    assert result.report is not None
    assert result.report.total == 4


def test_run_pipeline_scored_list_matches_diffs():
    result = run_pipeline(BEFORE, AFTER)
    assert len(result.scored) == result.total


def test_run_pipeline_annotated_populated_by_default():
    result = run_pipeline(BEFORE, AFTER)
    assert len(result.annotated) > 0


def test_run_pipeline_tagged_populated_by_default():
    result = run_pipeline(BEFORE, AFTER)
    assert len(result.tagged) > 0


def test_run_pipeline_no_annotate_flag():
    config = PipelineConfig(annotate=False)
    result = run_pipeline(BEFORE, AFTER, config=config)
    assert result.annotated == []


def test_run_pipeline_no_tag_flag():
    config = PipelineConfig(tag=False)
    result = run_pipeline(BEFORE, AFTER, config=config)
    assert result.tagged == []


def test_run_pipeline_include_fields_filters_changes():
    config = PipelineConfig(include_fields=["status"])
    result = run_pipeline(BEFORE, AFTER, config=config)
    for diff in result.diffs:
        for change in diff.changes:
            assert change.field == "status"


def test_run_pipeline_min_score_filters_low_scoring():
    config = PipelineConfig(min_score=999.0)
    result = run_pipeline(BEFORE, AFTER, config=config)
    # No diff should exceed an absurdly high score
    assert len(result.scored) == 0


def test_run_pipeline_default_config_used_when_none():
    result = run_pipeline(BEFORE, AFTER, config=None)
    assert result.total >= 0


def test_pipeline_config_defaults():
    cfg = PipelineConfig()
    assert cfg.min_score == 0.0
    assert cfg.annotate is True
    assert cfg.tag is True
    assert cfg.include_fields is None
