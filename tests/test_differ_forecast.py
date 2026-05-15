"""Tests for logdiff.differ_forecast."""

from __future__ import annotations

import pytest

from logdiff.differ_forecast import (
    ForecastError,
    FieldForecast,
    ForecastPoint,
    _linear_forecast,
    build_forecast,
)


# ---------------------------------------------------------------------------
# _linear_forecast
# ---------------------------------------------------------------------------

def test_linear_forecast_empty_history_raises():
    with pytest.raises(ForecastError, match="History"):
        _linear_forecast([], steps=3)


def test_linear_forecast_single_point_flat():
    pts = _linear_forecast([5], steps=2)
    assert len(pts) == 2
    for pt in pts:
        assert pt.predicted_changes == pytest.approx(5.0)


def test_linear_forecast_growing_series():
    pts = _linear_forecast([1, 2, 3, 4], steps=2)
    assert pts[0].predicted_changes > 4.0
    assert pts[1].predicted_changes > pts[0].predicted_changes


def test_linear_forecast_declining_series_clamped_at_zero():
    pts = _linear_forecast([10, 5, 0], steps=3)
    for pt in pts:
        assert pt.predicted_changes >= 0.0


def test_linear_forecast_confidence_decays():
    pts = _linear_forecast([2, 4, 6], steps=4, decay=0.1)
    confidences = [pt.confidence for pt in pts]
    assert confidences == sorted(confidences, reverse=True)


def test_linear_forecast_confidence_not_negative():
    pts = _linear_forecast([1, 1, 1], steps=20, decay=0.1)
    for pt in pts:
        assert pt.confidence >= 0.0


def test_linear_forecast_step_numbers_sequential():
    pts = _linear_forecast([3, 6], steps=3)
    assert [pt.step for pt in pts] == [1, 2, 3]


# ---------------------------------------------------------------------------
# build_forecast
# ---------------------------------------------------------------------------

def test_build_forecast_empty_raises():
    with pytest.raises(ForecastError, match="No field histories"):
        build_forecast({})


def test_build_forecast_steps_zero_raises():
    with pytest.raises(ForecastError, match="steps"):
        build_forecast({"x": [1, 2]}, steps=0)


def test_build_forecast_skips_short_history():
    result = build_forecast({"a": [1], "b": [1, 2, 3]}, min_history=2)
    names = [f.field_name for f in result]
    assert "a" not in names
    assert "b" in names


def test_build_forecast_returns_field_forecast_instances():
    result = build_forecast({"cpu": [3, 6, 9]}, steps=2)
    assert len(result) == 1
    assert isinstance(result[0], FieldForecast)
    assert len(result[0].points) == 2


def test_build_forecast_sorted_by_slope_descending():
    histories = {
        "slow": [1, 2, 3],
        "fast": [1, 5, 9],
        "flat": [4, 4, 4],
    }
    result = build_forecast(histories, steps=1)
    slopes = [abs(f.trend_slope) for f in result]
    assert slopes == sorted(slopes, reverse=True)


# ---------------------------------------------------------------------------
# FieldForecast helpers
# ---------------------------------------------------------------------------

def test_field_forecast_is_growing_true():
    ff = FieldForecast(
        field_name="x",
        history=[1, 2, 3],
        points=[
            ForecastPoint(step=1, predicted_changes=4.0, confidence=0.9),
            ForecastPoint(step=2, predicted_changes=5.0, confidence=0.8),
        ],
    )
    assert ff.is_growing is True


def test_field_forecast_is_growing_false_when_single_point():
    ff = FieldForecast(
        field_name="x",
        history=[3],
        points=[ForecastPoint(step=1, predicted_changes=3.0, confidence=1.0)],
    )
    assert ff.is_growing is False


def test_field_forecast_trend_slope_flat():
    ff = FieldForecast(field_name="y", history=[5, 5, 5])
    assert ff.trend_slope == pytest.approx(0.0)


def test_field_forecast_trend_slope_positive():
    ff = FieldForecast(field_name="z", history=[0, 1, 2, 3])
    assert ff.trend_slope > 0
