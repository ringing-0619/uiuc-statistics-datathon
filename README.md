# UIUC Statistics Datathon

English | [简体中文](README.zh-CN.md)

A reproducible call-center forecasting demo adapted from a UIUC Statistics Datathon team project.

**Python · pandas · NumPy · scikit-learn · openpyxl**

## Project at a glance

- **Task:** Forecast call demand at daily and half-hour resolution, alongside call care time (CCT) and abandon rates, to explore a demand-planning workflow.
- **Daily forecasting:** Fit gradient-boosting models by group using calendar features, then apply historical residual calibration and a configurable planning bias.
- **Intraday allocation:** Distribute daily volumes across 48 half-hour slots using normalized weekday profiles; estimate CCT and abandon rates through separate profiles and historical level heuristics.
- **Evaluation:** Refit the daily-volume model for two chronological monthly backtests, using only earlier observations for each fold. MAE and WAPE remain in memory; this evaluates the daily component.

## Run the synthetic demo

Verified with Python 3.13. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --demo
```

On Windows, activate with `.venv\Scripts\activate`.

The demo independently generates inputs for four fictional groups and writes `outputs/demo/synthetic_forecast.csv`. No competition files or credentials are required. After installation, execution is offline, with no tracking server or artifact uploads. Add `--evaluate` to run the optional backtests; metrics are not printed or saved.

## Verification

**18 regression tests** cover reproducible generation, chronological splits, Excel input, output validation, and privacy safeguards. Exports are checked for complete calendar coverage, finite/nonnegative metrics, bounded rates, and consistent abandoned-call counts.

```bash
python -B -m unittest discover -s tests -v
```

## Data and scope

Competition records, derived business statistics, trained artifacts, and original submissions are excluded. Synthetic results demonstrate software behavior, not competition accuracy or operational gains. No competition score or ranking is claimed.

[Run guide](docs/user-guide.md) · [Methodology and limitations](docs/methodology.md) · [Data policy and licensing boundaries](docs/data_policy.md)
