"""Shared synthetic-only fixtures and temporary files contained in this copy."""
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from config import DEMO_FORECAST_MONTH, DEMO_FORECAST_YEAR
from synthetic_data import generate_demo_data
from cv_model import run_cv_pipeline
from intraday import build_all_profiles
from cct_abd import compute_daily_scale_factors, compute_interval_means
from forecast import assemble


@lru_cache(maxsize=1)
def demo_inputs():
    return generate_demo_data()


@lru_cache(maxsize=1)
def demo_forecast():
    daily, interval = demo_inputs()
    year, month = DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH
    _, predictions, _ = run_cv_pipeline(daily, year, month)
    return assemble(predictions, build_all_profiles(interval),
                    compute_daily_scale_factors(daily, year, month),
                    compute_interval_means(interval), year, month)


@contextmanager
def local_tempdir():
    parent = ROOT / ".test-tmp"
    parent.mkdir(exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            yield Path(directory)
    finally:
        try:
            parent.rmdir()
        except OSError:
            pass
