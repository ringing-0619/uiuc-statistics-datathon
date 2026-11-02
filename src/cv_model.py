"""Daily forecasts with calendar features and historical residual calibration.

The previous year's same-month actual/predicted ratio is a calibration heuristic,
not an independently estimated year-over-year growth forecast. Optional rolling
validation refits the daily-volume pipeline strictly before each validation month.
No observed means, predictions or evaluation metrics are printed or saved here.
"""
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

from config import BACKTEST_MONTHS, CV_BIAS, GBM_PARAMS, PORTFOLIOS


def month_dates(year: int, month: int) -> pd.DatetimeIndex:
    start = pd.Timestamp(year=year, month=month, day=1)
    return pd.date_range(start, start + pd.offsets.MonthEnd(0), freq="D")


def _build_X(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "DOW": frame["DOW"], "Month": frame["Month"], "Day": frame["Day"],
        "Is_Weekend": frame["Is_Weekend"], "Is_Holiday": frame["Is_Holiday"],
        "DOW_x_Month": frame["DOW"] * frame["Month"],
    }, index=frame.index)


def train(history: pd.DataFrame) -> GradientBoostingRegressor:
    if history.empty or not np.isfinite(history["CV"].to_numpy()).all():
        raise ValueError("Training requires nonempty, finite daily call volumes.")
    model = GradientBoostingRegressor(**GBM_PARAMS)
    model.fit(_build_X(history), history["CV"].to_numpy())
    return model


def _calibration_ratios(model, history: pd.DataFrame, year: int, month: int) -> np.ndarray:
    reference = history[(history["Year"] == year - 1) & (history["Month"] == month)].copy()
    ratios = np.ones(7)
    if reference.empty:
        return ratios
    reference["prediction"] = model.predict(_build_X(reference))
    for dow in range(7):
        subset = reference[reference["DOW"] == dow]
        predicted = subset["prediction"].mean()
        if not subset.empty and predicted > 0:
            ratios[dow] = subset["CV"].mean() / predicted
    if not np.isfinite(ratios).all():
        raise ValueError("Historical calibration produced invalid factors.")
    return ratios


def predict_month(model, history: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    dates = month_dates(year, month)
    if history.empty or history["Date"].max() >= dates[0]:
        raise ValueError("Prediction history must end before the forecast month.")
    holidays = USFederalHolidayCalendar().holidays(dates[0], dates[-1])
    frame = pd.DataFrame({
        "Date": dates, "DOW": dates.dayofweek, "Month": month, "Day": dates.day,
        "Is_Weekend": (dates.dayofweek >= 5).astype(int),
        "Is_Holiday": dates.isin(holidays).astype(int),
    })
    frame["CV_raw"] = model.predict(_build_X(frame))
    ratios = _calibration_ratios(model, history, year, month)
    frame["CV_corrected"] = frame["CV_raw"] * ratios[frame["DOW"].to_numpy()]
    frame["CV_final"] = (frame["CV_corrected"] * CV_BIAS).clip(lower=0)
    return frame[["Date", "DOW", "CV_raw", "CV_corrected", "CV_final"]]


def evaluate(history: pd.DataFrame, n_months: int = BACKTEST_MONTHS) -> dict:
    """Evaluate daily CV including calibration and bias; keep results in memory.

    This is not an end-to-end evaluation of intraday CCT/ABD. An all-zero actual
    validation month has undefined WAPE, represented by None.
    """
    if n_months < 1:
        raise ValueError("At least one backtest month is required.")
    frame = history.sort_values("Date")
    periods = sorted(frame["Date"].dt.to_period("M").unique())
    if len(periods) < n_months + 12:
        raise ValueError("More calendar history is required for rolling validation.")
    folds = []
    for period in periods[-n_months:]:
        start = period.start_time
        training = frame[frame["Date"] < start]
        validation = frame[frame["Date"].dt.to_period("M") == period]
        if training.empty or len(validation) != period.days_in_month:
            raise ValueError("Backtest months must be complete and follow training data.")
        model = train(training)
        prediction = predict_month(model, training, period.year, period.month)
        aligned = validation[["Date", "CV"]].merge(
            prediction[["Date", "CV_final"]], on="Date", validate="one_to_one"
        )
        actual, predicted = aligned["CV"].to_numpy(), aligned["CV_final"].to_numpy()
        denominator = float(actual.sum())
        folds.append({
            "train_end": training["Date"].max().date().isoformat(),
            "validation_start": start.date().isoformat(),
            "validation_end": validation["Date"].max().date().isoformat(),
            "mae": float(mean_absolute_error(actual, predicted)),
            "wape": float(np.abs(actual - predicted).sum() / denominator) if denominator else None,
        })
    return {"component": "daily_cv", "folds": folds}


def run_cv_pipeline(daily: dict, year: int, month: int, *, backtest: bool = False) -> tuple:
    models, predictions, metrics = {}, {}, {}
    start = month_dates(year, month)[0]
    for group in PORTFOLIOS:
        history = daily[group]
        if history["Date"].max() >= start:
            raise ValueError("Daily inputs must precede the requested forecast month.")
        metrics[group] = evaluate(history) if backtest else {}
        model = train(history)
        models[group] = model
        predictions[group] = predict_month(model, history, year, month)
    return models, predictions, metrics
