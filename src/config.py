"""Public configuration; no observations from the confidential dataset."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
PORTFOLIOS = ("group_1", "group_2", "group_3", "group_4")
SLOTS_PER_DAY = 48

# Arbitrary demonstration dates, unrelated to the competition forecast period.
DEMO_FORECAST_YEAR = 2030
DEMO_FORECAST_MONTH = 3
DEMO_SEED = 42

# Algorithm settings, not observed business statistics.
GBM_PARAMS = {
    "n_estimators": 400, "learning_rate": 0.04, "max_depth": 4,
    "min_samples_leaf": 5, "subsample": 0.8, "random_state": 42,
}
CV_BIAS = 1.06
BACKTEST_MONTHS = 2
