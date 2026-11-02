"""Run an offline synthetic demo or an explicitly supplied local workbook."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import DEMO_FORECAST_MONTH, DEMO_FORECAST_YEAR, DEMO_SEED, OUTPUT_DIR
from data_loader import load_all
from cv_model import month_dates, run_cv_pipeline
from intraday import build_all_profiles
from cct_abd import compute_daily_scale_factors, compute_interval_means
from forecast import assemble, save
from synthetic_data import generate_demo_data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Use independently generated synthetic data (the default).")
    mode.add_argument("--data", type=Path, help="Explicit local workbook using the public example schema.")
    parser.add_argument("--forecast-year", type=int)
    parser.add_argument("--forecast-month", type=int, choices=range(1, 13))
    parser.add_argument("--seed", type=int, default=DEMO_SEED, help="Synthetic generator seed.")
    parser.add_argument("--evaluate", action="store_true", help="Run historical daily-volume backtests; keep metrics in memory.")
    parser.add_argument("--output-dir", type=Path, help="Local result directory; generated files must remain private when using real data.")
    args = parser.parse_args(argv)
    synthetic = args.data is None
    if not synthetic and (args.forecast_year is None or args.forecast_month is None):
        parser.error("--data requires an explicit --forecast-year and --forecast-month")
    year = args.forecast_year if args.forecast_year is not None else DEMO_FORECAST_YEAR
    month = args.forecast_month if args.forecast_month is not None else DEMO_FORECAST_MONTH
    try:
        start = month_dates(year, month)[0]
        if synthetic:
            daily, interval = generate_demo_data(args.seed, year)
        else:
            daily, interval = load_all(args.data)
        if any(frame["Date"].max() >= start for frame in interval.values()):
            raise ValueError("Interval inputs must precede the requested forecast month.")
        profiles = build_all_profiles(interval)
        _, predictions, _ = run_cv_pipeline(daily, year, month, backtest=args.evaluate)
        scales = compute_daily_scale_factors(daily, year, month)
        means = compute_interval_means(interval)
        forecast = assemble(predictions, profiles, scales, means, year, month)
        output_dir = args.output_dir if args.output_dir is not None else OUTPUT_DIR / ("demo" if synthetic else "private")
        filename = "synthetic_forecast.csv" if synthetic else "private_forecast.csv"
        save(forecast, output_dir / filename, year, month)
    except (ValueError, FileNotFoundError) as error:
        parser.exit(1, f"Pipeline stopped: {error}\n")
    if synthetic:
        print("Synthetic demo completed. The forecast is generated data, not competition results.")
    else:
        print("Local workbook run completed. Keep the generated forecast private.")
    if args.evaluate:
        print("Daily-volume backtesting completed; metrics were not printed or saved.")
    print("Output saved locally. No experiment tracking or network upload is performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
