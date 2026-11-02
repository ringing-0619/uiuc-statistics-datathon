"""Assemble a generic monthly forecast and reject invalid output before saving."""
from pathlib import Path
import calendar

import numpy as np
import pandas as pd

from config import PORTFOLIOS, SLOTS_PER_DAY
from cv_model import month_dates
from intraday import SLOT_LABELS


def output_columns() -> list[str]:
    return ["Month", "Day", "Interval"] + [
        f"{metric}_{group}" for group in PORTFOLIOS
        for metric in ("Calls_Offered", "Abandoned_Calls", "Abandoned_Rate", "CCT")
    ]


def assemble(predictions: dict, profiles: dict, daily_scales: dict,
             interval_means: dict, year: int, month: int) -> pd.DataFrame:
    rows = []
    dates = month_dates(year, month)
    for group in PORTFOLIOS:
        actual_dates = pd.DatetimeIndex(predictions[group]["Date"])
        if not actual_dates.equals(dates):
            raise ValueError("Daily predictions must exactly cover the requested month.")
    for day_index, date in enumerate(dates):
        dow = date.dayofweek
        for slot_index, slot in enumerate(SLOT_LABELS):
            row = {"Month": calendar.month_name[month], "Day": date.day, "Interval": slot}
            for group in PORTFOLIOS:
                daily_cv = float(predictions[group].iloc[day_index]["CV_final"])
                profile = profiles[group]
                means, scale = interval_means[group], daily_scales[group]
                cct_factor = scale["cct_target"] / means["cct_interval"] if means["cct_interval"] > 0 else 1.0
                abd_factor = scale["abd_target"] / means["abd_interval"] if means["abd_interval"] > 0 else 1.0
                cv = round(max(daily_cv * profile["cv"][dow][slot_index], 0), 2)
                cct = round(max(profile["cct"][dow][slot_index] * cct_factor, 0), 2)
                abd = round(float(np.clip(profile["abd"][dow][slot_index] * abd_factor, 0, 1)), 6)
                row[f"Calls_Offered_{group}"] = cv
                row[f"Abandoned_Calls_{group}"] = int(round(abd * cv))
                row[f"Abandoned_Rate_{group}"] = abd
                row[f"CCT_{group}"] = cct
            rows.append(row)
    return pd.DataFrame(rows, columns=output_columns())


def validate(frame: pd.DataFrame, year: int, month: int) -> None:
    """Fail without revealing row contents; check the entire output time grid."""
    if list(frame.columns) != output_columns():
        raise ValueError("Forecast columns do not match the public output schema.")
    dates = month_dates(year, month)
    if len(frame) != len(dates) * SLOTS_PER_DAY:
        raise ValueError("Forecast row count does not match the requested month.")
    numeric = ["Day", *output_columns()[3:]]
    if any(not pd.api.types.is_numeric_dtype(frame[c]) or pd.api.types.is_bool_dtype(frame[c]) for c in numeric):
        raise ValueError("Forecast metrics and days must be numeric.")
    values = frame[numeric].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Forecast contains missing, infinite or negative values.")
    if not frame["Month"].eq(calendar.month_name[month]).all():
        raise ValueError("Forecast month labels do not match the requested month.")
    if not frame["Day"].eq(frame["Day"].round()).all():
        raise ValueError("Forecast day numbers must be integers.")
    keys = pd.MultiIndex.from_frame(frame[["Day", "Interval"]])
    expected = pd.MultiIndex.from_product([range(1, len(dates) + 1), SLOT_LABELS])
    if keys.has_duplicates or set(keys) != set(expected):
        raise ValueError("Forecast has duplicate, missing or invalid date/time keys.")
    for group in PORTFOLIOS:
        cv = frame[f"Calls_Offered_{group}"]
        abd = frame[f"Abandoned_Rate_{group}"]
        abandoned = frame[f"Abandoned_Calls_{group}"]
        if (abd > 1).any():
            raise ValueError("Forecast abandon rates must be between zero and one.")
        if not abandoned.eq(abandoned.round()).all():
            raise ValueError("Abandoned call counts must be integers.")
        if not np.array_equal(abandoned.to_numpy(), np.rint((cv * abd).to_numpy())):
            raise ValueError("Abandoned call counts do not agree with volume and rate.")


def save(frame: pd.DataFrame, path: str | Path, year: int, month: int) -> None:
    validate(frame, year, month)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
