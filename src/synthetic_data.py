"""Independently generated software-test examples, unrelated to private records.

All constants below are arbitrary demo choices. The generator does not read a
competition workbook, fitted model, tracking database or observed business stats.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from config import DEMO_FORECAST_YEAR, DEMO_SEED, PORTFOLIOS
from data_loader import parse_daily, parse_interval
from intraday import SLOT_LABELS


def generate_demo_data(seed: int = DEMO_SEED, forecast_year: int = DEMO_FORECAST_YEAR) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(f"{forecast_year - 2}-01-01", f"{forecast_year - 1}-12-31")
    interval_dates = pd.date_range(f"{forecast_year - 1}-01-01", periods=56)
    daily, interval = {}, {}
    time_index = np.arange(len(dates))
    slots = np.arange(48)
    weights = 1 + 0.18 * np.cos(2 * np.pi * (slots + 3) / 48)
    weights /= weights.sum()
    for index, group in enumerate(PORTFOLIOS):
        expected = 1200 + 180 * index + 45 * dates.dayofweek + 60 * np.sin(time_index / 29)
        raw_daily = pd.DataFrame({
            "Date": dates,
            "CV": rng.poisson(expected),
            "CCT": np.clip(110 + 9 * index + rng.normal(0, 3, len(dates)), 1, None),
            "ABD": rng.uniform(0.01, 0.04, len(dates)),
        })
        totals = rng.poisson(1200 + 180 * index, len(interval_dates))
        count = len(interval_dates) * 48
        raw_interval = pd.DataFrame({
            "Date": interval_dates.repeat(48),
            "Interval": np.tile(SLOT_LABELS, len(interval_dates)),
            "CV": rng.poisson(np.repeat(totals, 48) * np.tile(weights, len(interval_dates))),
            "CCT": np.clip(110 + 9 * index + rng.normal(0, 3, count), 1, None),
            "ABD": rng.uniform(0.01, 0.04, count),
        })
        daily[group] = parse_daily(raw_daily)
        interval[group] = parse_interval(raw_interval)
    return daily, interval


def write_demo_workbook(path: str | Path, seed: int = DEMO_SEED,
                        forecast_year: int = DEMO_FORECAST_YEAR) -> None:
    daily, interval = generate_demo_data(seed, forecast_year)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for group in PORTFOLIOS:
            daily[group][["Date", "CV", "CCT", "ABD"]].to_excel(
                writer, sheet_name=f"{group}_daily", index=False
            )
            interval[group][["Date", "Interval", "CV", "CCT", "ABD"]].to_excel(
                writer, sheet_name=f"{group}_interval", index=False
            )
