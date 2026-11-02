"""Separate CCT and abandon-rate level heuristics.

Historical same-month means set daily levels; interval profiles set the shape.
These are modeling choices, not claims about confidential correlations or trends.
"""
import numpy as np

from config import PORTFOLIOS


def _month_mean(frame, column: str, year: int, month: int) -> float:
    subset = frame[(frame["Year"] == year) & (frame["Month"] == month)]
    value = float(subset[column].mean())
    if not np.isfinite(value):
        raise ValueError("Historical same-month data is required for level scaling.")
    return value


def compute_daily_scale_factors(daily: dict, year: int, month: int) -> dict:
    scales = {}
    for group in PORTFOLIOS:
        frame = daily[group]
        cct_previous = _month_mean(frame, "CCT", year - 2, month)
        cct_recent = _month_mean(frame, "CCT", year - 1, month)
        cct_ratio = cct_recent / cct_previous if cct_previous > 0 else 1.0
        abd_previous = _month_mean(frame, "ABD", year - 2, month)
        abd_recent = _month_mean(frame, "ABD", year - 1, month)
        scales[group] = {
            "cct_target": max(cct_recent * cct_ratio, 0.0),
            "abd_target": float(np.clip(max(abd_previous, abd_recent), 0, 1)),
        }
    return scales


def compute_interval_means(interval: dict) -> dict:
    means = {}
    for group in PORTFOLIOS:
        frame = interval[group]
        cct, abd = float(frame["CCT"].mean()), float(frame["ABD"].mean())
        if not np.isfinite([cct, abd]).all():
            raise ValueError("Interval scaling requires finite input metrics.")
        means[group] = {"cct_interval": cct, "abd_interval": abd}
    return means
