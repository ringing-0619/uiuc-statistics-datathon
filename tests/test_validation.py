import calendar
import datetime as dt
import unittest

import numpy as np
import pandas as pd

from common import demo_forecast, demo_inputs, local_tempdir
from config import DEMO_FORECAST_MONTH, DEMO_FORECAST_YEAR, PORTFOLIOS
from cv_model import month_dates, run_cv_pipeline
from data_loader import _interval_to_hour, parse_daily, parse_interval
from forecast import output_columns, save, validate
from intraday import SLOT_LABELS, build_all_profiles


class ValidationTests(unittest.TestCase):
    def test_missing_infinite_negative_and_inconsistent_values_are_rejected(self):
        group = PORTFOLIOS[0]
        mutations = [
            (f"Calls_Offered_{group}", np.nan), (f"CCT_{group}", np.nan),
            (f"CCT_{group}", np.inf), (f"Calls_Offered_{group}", -1.0),
            (f"Abandoned_Rate_{group}", 1.1), (f"Abandoned_Rate_{group}", -0.1),
            (f"Abandoned_Calls_{group}", 0.5),
            (f"Abandoned_Calls_{group}", 1_000_000), ("Day", 1.5),
        ]
        for column, value in mutations:
            with self.subTest(column=column, value=value):
                frame = demo_forecast().copy()
                frame[column] = frame[column].astype(float)
                frame.loc[0, column] = value
                with self.assertRaises(ValueError):
                    validate(frame, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)

    def test_missing_duplicate_invalid_keys_and_columns_are_rejected(self):
        original = demo_forecast()
        cases = [original.iloc[:-1].copy(), original.drop(columns=["Interval"]),
                 original.assign(unexpected=1)]
        duplicate = original.copy()
        duplicate.loc[1, ["Day", "Interval"]] = duplicate.loc[0, ["Day", "Interval"]].values
        cases.append(duplicate)
        for column, value in [("Interval", "25:00"), ("Month", "invalid"), ("Day", 0)]:
            frame = original.copy()
            frame.loc[0, column] = value
            cases.append(frame)
        for index, frame in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                validate(frame, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)

    def test_failed_validation_neither_creates_nor_overwrites_a_file(self):
        invalid = demo_forecast().iloc[:-1].copy()
        with local_tempdir() as directory:
            path = directory / "forecast.csv"
            with self.assertRaises(ValueError):
                save(invalid, path, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)
            self.assertFalse(path.exists())
            path.write_text("existing local example", encoding="utf-8")
            with self.assertRaises(ValueError):
                save(invalid, path, DEMO_FORECAST_YEAR, DEMO_FORECAST_MONTH)
            self.assertEqual(path.read_text(), "existing local example")

    def test_grid_validation_supports_short_months_and_leap_years(self):
        for year, month in [(2031, 2), (2032, 2), (2030, 4), (2030, 3)]:
            records = []
            for date in month_dates(year, month):
                for slot in SLOT_LABELS:
                    record = {column: 0 for column in output_columns()[3:]}
                    record.update(Month=calendar.month_name[month], Day=date.day, Interval=slot)
                    records.append(record)
            frame = pd.DataFrame(records, columns=output_columns())
            with self.subTest(year=year, month=month):
                validate(frame, year, month)

    def test_text_excel_time_and_numeric_time_slots_are_supported(self):
        for value in ["9:30", "09:30:00", dt.time(9, 30), 9.5 / 24]:
            with self.subTest(kind=type(value).__name__):
                self.assertEqual(_interval_to_hour(value), 9.5)
        for value in ["bad", "24:00", "9:15", dt.time(9, 30, 1), np.nan, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                _interval_to_hour(value)
        raw = demo_inputs()[1][PORTFOLIOS[0]].copy()
        parsed = parse_interval(raw)
        self.assertEqual(len(raw), len(parsed))
        raw.loc[0, "Interval"] = "bad"
        with self.assertRaises(ValueError):
            parse_interval(raw)

    def test_near_midnight_excel_fraction_cannot_become_next_day(self):
        with self.assertRaises(ValueError):
            _interval_to_hour(np.nextafter(1.0, 0.0))
        self.assertEqual(_interval_to_hour(47 / 48), 23.5)

    def test_invalid_input_values_dates_and_duplicate_keys_are_rejected(self):
        raw_daily = demo_inputs()[0][PORTFOLIOS[0]]
        for column, value in [("CV", np.nan), ("ABD", 2), ("Date", "invalid")]:
            raw = raw_daily.copy()
            raw[column] = raw[column].astype(object)
            raw.loc[0, column] = value
            with self.subTest(column=column), self.assertRaises(ValueError):
                parse_daily(raw)
        with self.assertRaises(ValueError):
            parse_daily(pd.concat([raw_daily, raw_daily.iloc[[0]]], ignore_index=True))
        raw_interval = demo_inputs()[1][PORTFOLIOS[0]]
        with self.assertRaises(ValueError):
            parse_interval(pd.concat([raw_interval, raw_interval.iloc[[0]]], ignore_index=True))

    def test_future_history_and_zero_volume_profiles_fail_explicitly(self):
        daily, interval = demo_inputs()
        with self.assertRaises(ValueError):
            run_cv_pipeline(daily, DEMO_FORECAST_YEAR - 1, 1)
        zeros = {group: frame.assign(CV=0) for group, frame in interval.items()}
        with self.assertRaises(ValueError):
            build_all_profiles(zeros)


if __name__ == "__main__":
    unittest.main()
