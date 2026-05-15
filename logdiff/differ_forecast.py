"""Forecast future field change rates based on historical trend data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class ForecastError(Exception):
    """Raised when forecasting cannot be performed."""


@dataclass
class ForecastPoint:
    """A single projected data point."""

    step: int
    predicted_changes: float
    confidence: float  # 0.0 – 1.0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ForecastPoint(step={self.step}, "
            f"predicted={self.predicted_changes:.2f}, "
            f"confidence={self.confidence:.2f})"
        )


@dataclass
class FieldForecast:
    """Forecast for a single field."""

    field_name: str
    history: List[int]
    points: List[ForecastPoint] = field(default_factory=list)

    @property
    def is_growing(self) -> bool:
        if len(self.points) < 2:
            return False
        return self.points[-1].predicted_changes > self.points[0].predicted_changes

    @property
    def trend_slope(self) -> float:
        """Linear slope across history values."""
        n = len(self.history)
        if n < 2:
            return 0.0
        xs = list(range(n))
        x_mean = sum(xs) / n
        y_mean = sum(self.history) / n
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, self.history))
        denominator = sum((x - x_mean) ** 2 for x in xs)
        return numerator / denominator if denominator else 0.0


def _linear_forecast(
    history: List[int], steps: int, decay: float = 0.05
) -> List[ForecastPoint]:
    """Project `steps` future values using a simple linear extrapolation."""
    n = len(history)
    if n == 0:
        raise ForecastError("History must contain at least one data point.")
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(history) / n
    denom = sum((x - x_mean) ** 2 for x in xs) or 1.0
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, history)) / denom
    intercept = y_mean - slope * x_mean
    points: List[ForecastPoint] = []
    for s in range(1, steps + 1):
        predicted = max(0.0, slope * (n - 1 + s) + intercept)
        confidence = max(0.0, 1.0 - decay * s)
        points.append(ForecastPoint(step=s, predicted_changes=predicted, confidence=confidence))
    return points


def build_forecast(
    field_histories: dict[str, List[int]],
    steps: int = 3,
    min_history: int = 2,
) -> List[FieldForecast]:
    """Build forecasts for each field given its change-count history."""
    if not field_histories:
        raise ForecastError("No field histories provided.")
    if steps < 1:
        raise ForecastError("steps must be >= 1.")
    results: List[FieldForecast] = []
    for fname, history in field_histories.items():
        if len(history) < min_history:
            continue
        pts = _linear_forecast(history, steps)
        results.append(FieldForecast(field_name=fname, history=list(history), points=pts))
    results.sort(key=lambda f: abs(f.trend_slope), reverse=True)
    return results
