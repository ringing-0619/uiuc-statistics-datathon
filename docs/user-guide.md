# Running the public forecasting demo

[Project overview](../README.md) · [项目概览（中文）](../README.zh-CN.md)

A public adaptation of a call-center forecasting workflow developed for the UIUC Statistics Datathon. It demonstrates calendar-based daily forecasting, half-hour allocation and separate care-time/abandon-rate scaling.

**All demonstration data is independently generated. No competition records, observed business statistics, trained models, tracking databases or submission artifacts are distributed. Demo dates and group names are arbitrary and have no private dataset mapping.** This is a revised demonstration, not the original submission or a claim of competition accuracy.

## Quick start

Python 3.13 is the release verification target. Run these commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --demo
```

On Windows, activate with `.venv\Scripts\activate`.

The demo creates `outputs/demo/synthetic_forecast.csv`. It runs locally and does not require credentials, competition files, a tracking server or internet access after installation. Running `python main.py` also defaults to the synthetic demo.

```bash
# Optional rolling backtests of the daily call-volume component
python main.py --demo --evaluate

# Behavioral and regression checks; unittest is part of Python
python -m unittest discover -s tests -v
```

Backtest results stay in memory. The CLI prints completion messages without input summaries, business means, predictions or evaluation values. MLflow logging and artifact uploads have been removed from this public adaptation; a tracking URI in the environment cannot redirect its outputs.

## Method

1. Fit a gradient-boosting regressor for each generic group using calendar features.
2. Calibrate daily predictions using historical same-month residual ratios, then apply a configurable planning bias. The ratio is not an independently estimated growth forecast.
3. Allocate daily volumes using day-of-week half-hour share profiles.
4. Scale separate care-time and abandon-rate profiles using historical level heuristics.
5. Validate the full calendar grid, finite/nonnegative metrics, bounded rates and internally consistent abandoned-call counts before saving.

See [methodology](methodology.md) for evaluation scope, assumptions and limitations. No score, ranking or business outcome is asserted in this repository.

## Optional example workbook

The default demo generates inputs in memory. To exercise Excel input separately:

```bash
python scripts/generate_synthetic_data.py
python main.py --data data/synthetic/demo.xlsx --forecast-year 2030 --forecast-month 3 --output-dir outputs/workbook-demo
```

A `--data` run always treats the supplied workbook as private, even when it is a synthetic example, and writes `private_forecast.csv`. It requires an explicit forecast year and month. The public example schema is documented in [data policy](data_policy.md); it is not an adapter for the confidential competition workbook. Source staffing sheets and submission templates are not required.

Use only data you are authorized to process. Inputs must precede the forecast month. Historical level scaling needs the target calendar month in each of the two previous years. Real inputs, generated forecasts and any locally inspected backtest results must remain private unless disclosure is explicitly permitted.

## Repository layout

```text
main.py                         command-line entry point
requirements.txt                pinned direct dependencies
src/config.py                   generic configuration and algorithm settings
src/data_loader.py              explicit workbook loading and input validation
src/cv_model.py                  daily models and chronological backtests
src/intraday.py                  runtime interval profiles
src/cct_abd.py                   care-time and abandon-rate level heuristics
src/forecast.py                  assembly and validation before export
src/synthetic_data.py            independent example generator
scripts/generate_synthetic_data.py  optional local Excel example
scripts/check_public_files.py    release artifact checks
tests/                          behavioral and privacy regression tests
docs/methodology.md              modeling and evaluation scope
docs/data_policy.md              public example schema and confidentiality rules
```

`data/`, `outputs/`, databases, logs, model artifacts, credentials and caches are excluded by `.gitignore`. A generated result is never automatically a publishable artifact. Before sharing a folder or archive manually, exclude generated files as well; ignore rules govern Git tracking, not manual copies.

After removing local generated artifacts, run `python scripts/check_public_files.py` to check the release folder. This catches common artifact types and credential patterns; it cannot decide whether a written business conclusion is confidential or publication is permitted.

## Release scope

Confirm the organizer's code-disclosure terms and team attribution before public publication. No open-source license is added because authority to license the team code has not been established. This repository does not grant rights to the confidential dataset.
