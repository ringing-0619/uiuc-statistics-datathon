"""Write an optional local synthetic workbook for the public example schema."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import BASE_DIR, DEMO_FORECAST_YEAR, DEMO_SEED
from synthetic_data import write_demo_workbook


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE_DIR / "data" / "synthetic" / "demo.xlsx")
    parser.add_argument("--seed", type=int, default=DEMO_SEED)
    parser.add_argument("--forecast-year", type=int, default=DEMO_FORECAST_YEAR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.overwrite:
        parser.error("Output already exists; choose a different path or use --overwrite.")
    write_demo_workbook(args.output, args.seed, args.forecast_year)
    print("Synthetic example workbook created locally. It contains no competition records.")


if __name__ == "__main__":
    main()
