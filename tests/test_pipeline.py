import contextlib
import io
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from common import ROOT, demo_forecast, demo_inputs, local_tempdir
from config import DEMO_FORECAST_MONTH, DEMO_FORECAST_YEAR, PORTFOLIOS
import cv_model
from data_loader import load_all
from forecast import validate
from synthetic_data import generate_demo_data, write_demo_workbook


class PipelineTests(unittest.TestCase):
    def test_full_synthetic_forecast_is_valid(self):
        result = demo_forecast()
        validate(result, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)
        self.assertTrue(np.isfinite(result.iloc[:, 3:].to_numpy()).all())

    def test_synthetic_seed_reproduces_without_private_inputs(self):
        first, _ = generate_demo_data(seed=17)
        second, _ = generate_demo_data(seed=17)
        different, _ = generate_demo_data(seed=18)
        pd.testing.assert_frame_equal(first[PORTFOLIOS[0]], second[PORTFOLIOS[0]])
        self.assertFalse(first[PORTFOLIOS[0]]["CV"].equals(different[PORTFOLIOS[0]]["CV"]))

    def test_backtests_fit_only_dates_before_each_validation_month(self):
        history = demo_inputs()[0][PORTFOLIOS[0]]
        fitted_history = []
        original_train = cv_model.train

        def record(frame):
            fitted_history.append(frame.copy())
            return original_train(frame)

        with patch.object(cv_model, "train", side_effect=record):
            metrics = cv_model.evaluate(history)
        self.assertEqual(len(metrics["folds"]), 2)
        for training, fold in zip(fitted_history, metrics["folds"]):
            start = pd.Timestamp(fold["validation_start"])
            self.assertTrue((training["Date"] < start).all())
            held_out_dates = history.loc[history["Date"] >= start, "Date"]
            self.assertTrue(set(training["Date"]).isdisjoint(held_out_dates))
            self.assertTrue(np.isfinite(fold["mae"]))

    def test_demo_cli_ignores_remote_tracking_environment(self):
        with local_tempdir() as directory:
            environment = os.environ.copy()
            environment.update({"MLFLOW_TRACKING_URI": "https://example.invalid/tracking",
                                "PYTHONDONTWRITEBYTECODE": "1"})
            result = subprocess.run(
                [sys.executable, "-B", "main.py", "--demo", "--output-dir", str(directory)],
                cwd=ROOT, env=environment, text=True, capture_output=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Synthetic demo completed", result.stdout)
            self.assertNotIn("group_1", result.stdout)
            self.assertNotIn("example.invalid", result.stdout + result.stderr)
            output = pd.read_csv(directory / "synthetic_forecast.csv")
            validate(output, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)
            self.assertEqual({path.name for path in directory.iterdir()}, {"synthetic_forecast.csv"})

    def test_example_excel_round_trip_and_explicit_workbook_cli(self):
        with local_tempdir() as directory:
            workbook = directory / "synthetic.xlsx"
            write_demo_workbook(workbook)
            daily, interval = load_all(workbook)
            expected_daily, expected_interval = demo_inputs()
            for group in PORTFOLIOS:
                pd.testing.assert_series_equal(daily[group]["CV"], expected_daily[group]["CV"], check_dtype=False)
                self.assertEqual(len(interval[group]), len(expected_interval[group]))
            result = subprocess.run(
                [sys.executable, "-B", "main.py", "--data", str(workbook),
                 "--forecast-year", str(DEMO_FORECAST_YEAR),
                 "--forecast-month", str(DEMO_FORECAST_MONTH),
                 "--output-dir", str(directory / "results")],
                cwd=ROOT, text=True, capture_output=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Keep the generated forecast private", result.stdout)
            output = pd.read_csv(directory / "results" / "private_forecast.csv")
            validate(output, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)

    def test_model_functions_do_not_print_data_summaries(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cv_model.run_cv_pipeline(demo_inputs()[0], DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)
        self.assertEqual(buffer.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
