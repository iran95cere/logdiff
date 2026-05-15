"""Tests for logdiff.differ_normalize."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_normalize import (
    NormalizeConfig,
    NormalizeError,
    normalize_diffs,
)


def make_change(field_name: str, before: object, after: object, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field_name, before=before, after=after, change_type=change_type)


def make_diff(key: str, *changes: FieldChange) -> EntryDiff:
    return EntryDiff(key=key, changes=list(changes))


# --- NormalizeConfig.get_normalizer ---

def test_get_normalizer_returns_none_for_unknown_field():
    config = NormalizeConfig(rules={"level": "lowercase"})
    assert config.get_normalizer("other") is None


def test_get_normalizer_returns_builtin():
    config = NormalizeConfig(rules={"level": "lowercase"})
    fn = config.get_normalizer("level")
    assert fn is not None
    assert fn("ERROR") == "error"


def test_get_normalizer_unknown_rule_raises():
    config = NormalizeConfig(rules={"level": "nonexistent"})
    with pytest.raises(NormalizeError, match="Unknown normalizer"):
        config.get_normalizer("level")


def test_get_normalizer_custom_takes_precedence():
    config = NormalizeConfig(
        rules={"level": "lowercase"},
        custom={"level": lambda v: "CUSTOM"},
    )
    fn = config.get_normalizer("level")
    assert fn("anything") == "CUSTOM"


# --- normalize_diffs ---

def test_normalize_diffs_empty_returns_empty():
    config = NormalizeConfig()
    assert normalize_diffs([], config) == []


def test_normalize_diffs_lowercase():
    config = NormalizeConfig(rules={"level": "lowercase"})
    diffs = [make_diff("req-1", make_change("level", "ERROR", "WARNING"))]
    result = normalize_diffs(diffs, config)
    assert result[0].changes[0].before == "error"
    assert result[0].changes[0].after == "warning"


def test_normalize_diffs_strip():
    config = NormalizeConfig(rules={"msg": "strip"})
    diffs = [make_diff("req-2", make_change("msg", "  hello  ", " world "))]
    result = normalize_diffs(diffs, config)
    assert result[0].changes[0].before == "hello"
    assert result[0].changes[0].after == "world"


def test_normalize_diffs_preserves_key():
    config = NormalizeConfig(rules={"code": "str"})
    diffs = [make_diff("entry-42", make_change("code", 200, 404))]
    result = normalize_diffs(diffs, config)
    assert result[0].key == "entry-42"


def test_normalize_diffs_none_values_unchanged():
    config = NormalizeConfig(rules={"level": "lowercase"})
    diffs = [make_diff("req-3", make_change("level", None, None, "removed"))]
    result = normalize_diffs(diffs, config)
    assert result[0].changes[0].before is None
    assert result[0].changes[0].after is None


def test_normalize_diffs_unmatched_field_unchanged():
    config = NormalizeConfig(rules={"level": "lowercase"})
    diffs = [make_diff("req-4", make_change("status", "OK", "FAIL"))]
    result = normalize_diffs(diffs, config)
    assert result[0].changes[0].before == "OK"
    assert result[0].changes[0].after == "FAIL"


def test_normalize_diffs_does_not_mutate_original():
    config = NormalizeConfig(rules={"level": "uppercase"})
    original = make_diff("req-5", make_change("level", "info", "debug"))
    normalize_diffs([original], config)
    assert original.changes[0].before == "info"
