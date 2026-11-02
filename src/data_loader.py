"""Validate a generic public example schema without printing data statistics.

The example format, dates and group labels have no private dataset mapping.
"""
import datetime as dt
from pathlib import Path
import re

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from config import PORTFOLIOS


def _require_columns(frame: pd.DataFrame, columns: set[str]) -> None:
    if frame.empty or not columns.issubset(frame.columns):
        raise ValueError("Input is empty or missing required public-schema columns.")


def _dates(values: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values.dtype):
        raise ValueError("Dates must be calendar dates, not numeric timestamps.")
    dates = pd.to_datetime(values, errors="coerce", format="mixed")
    if dates.isna().any() or dates.dt.tz is not None:
        raise ValueError("Input contains missing, invalid or timezone-aware dates.")
    if not dates.eq(dates.dt.normalize()).all():
        raise ValueError("Date values must identify days without a time component.")
    return dates


def _numeric_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    for column in ("CV", "CCT", "ABD"):
        if pd.api.types.is_bool_dtype(frame[column].dtype):
            raise ValueError("Boolean values cannot be used as input metrics.")
        values = pd.to_numeric(frame[column], errors="coerce").astype(float)
        if not np.isfinite(values.to_numpy()).all() or (values < 0).any():
            raise ValueError("Input metrics must be finite and nonnegative.")
        frame[column] = values
    if (frame["ABD"] > 1).any():
        raise ValueError("Abandon rates must be between zero and one.")
    return frame


def _add_date_features(frame: pd.DataFrame) -> pd.DataFrame:
    dates = frame["Date"]
    holidays = USFederalHolidayCalendar().holidays(dates.min(), dates.max())
    frame["DOW"] = dates.dt.dayofweek
    frame["Month"] = dates.dt.month
    frame["Year"] = dates.dt.year
    frame["Day"] = dates.dt.day
    frame["Is_Weekend"] = (frame["DOW"] >= 5).astype(int)
    frame["Is_Holiday"] = dates.isin(holidays).astype(int)
    return frame


def _interval_to_hour(value) -> float:
    """Accept Excel time cells, Excel fractions or HH:MM[:SS] text."""
    if isinstance(value, (dt.datetime, dt.time, pd.Timestamp)):
        hour, minute = value.hour, value.minute
        second = value.second + value.microsecond / 1_000_000
    elif isinstance(value, str):
        match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*", value)
        if not match:
            raise ValueError("Intervals must be valid half-hour time slots.")
        hour, minute, second = int(match[1]), int(match[2]), int(match[3] or 0)
    elif isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, (bool, np.bool_)):
        if not np.isfinite(value) or not 0 <= value < 1:
            raise ValueError("Excel time fractions must be between zero and one.")
        slot = float(value) * 48
        rounded_slot = round(slot)
        if not 0 <= rounded_slot < 48 or not np.isclose(slot, rounded_slot, atol=1e-8, rtol=0):
            raise ValueError("Intervals must align to a half-hour boundary.")
        return rounded_slot / 2
    else:
        raise ValueError("Intervals contain an unsupported or missing value.")
    if not 0 <= hour < 24 or minute not in (0, 30) or second != 0:
        raise ValueError("Intervals must be valid half-hour time slots.")
    return hour + minute / 60


def parse_daily(raw: pd.DataFrame) -> pd.DataFrame:
    _require_columns(raw, {"Date", "CV", "CCT", "ABD"})
    frame = raw.copy()
    frame["Date"] = _dates(frame["Date"])
    if frame["Date"].duplicated().any():
        raise ValueError("Daily input contains duplicate dates.")
    frame = _numeric_metrics(frame).sort_values("Date").reset_index(drop=True)
    return _add_date_features(frame)


def parse_interval(raw: pd.DataFrame) -> pd.DataFrame:
    _require_columns(raw, {"Date", "Interval", "CV", "CCT", "ABD"})
    frame = raw.copy()
    frame["Date"] = _dates(frame["Date"])
    frame["hour"] = frame["Interval"].map(_interval_to_hour)
    frame["slot_str"] = frame["hour"].map(
        lambda hour: f"{int(hour)}:{30 if hour % 1 else 0:02d}"
    )
    if frame.duplicated(["Date", "hour"]).any():
        raise ValueError("Interval input contains duplicate date/time keys.")
    frame = _numeric_metrics(frame).sort_values(["Date", "hour"]).reset_index(drop=True)
    return _add_date_features(frame)


def load_all(path: str | Path) -> tuple[dict, dict]:
    """Read only an explicitly supplied local public-schema workbook.

    No directory search, private default path, staffing sheet or template is used.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError("The explicitly supplied workbook does not exist.")
    names = [f"{group}_{kind}" for group in PORTFOLIOS for kind in ("daily", "interval")]
    sheets = pd.read_excel(path, sheet_name=names, engine="openpyxl")
    daily = {group: parse_daily(sheets[f"{group}_daily"]) for group in PORTFOLIOS}
    interval = {group: parse_interval(sheets[f"{group}_interval"]) for group in PORTFOLIOS}
    return daily, interval
