# Methodology and evaluation scope

The public adaptation preserves the workflow's main decomposition:

`interval call volume = predicted daily call volume × estimated interval share`

Calendar features are day of week, month, day of month, weekend/holiday indicators and a day-of-week/month interaction. US federal holiday dates are derived from pandas' public calendar; this is a generic modeling convention, not a claim about any business operating schedule.

Daily models use gradient boosting. Historical residual calibration uses the previous year's same-month actual/model-predicted ratio by weekday. This is a heuristic adjustment, not a measured future growth rate. The configurable planning bias is an algorithm setting, not an observed business statistic.

Intraday share profiles are estimated at runtime, normalized to sum to one, and pooled when a weekday group lacks examples. Care time and abandon rate use separate profiles. Care-time levels extrapolate a historical same-month ratio; abandon-rate levels use the larger of two historical same-month means. These are retained modeling choices. No private correlations, peak periods, magnitudes or empirical stability findings are encoded in the documentation.

## Chronological evaluation

`--evaluate` refits the daily-volume model separately for each of the last two complete historical calendar months. Each fold uses only records dated before the validation month. Residual calibration uses that fold's training history, and the planning bias is included in the evaluated predictions. A final model is then fit on all input history, which must precede the requested forecast month.

The returned in-memory results include fold dates, MAE and WAPE. WAPE is undefined when the sum of actual volumes is zero and is returned as `None`. Metrics are not printed, saved, uploaded or claimed as competition performance.

This backtest evaluates the daily-volume component only. It does not evaluate the final intraday CCT/abandon-rate pipeline, establish staffing savings or recreate the original competition evaluation. Synthetic data checks software behavior, not real-world predictive accuracy.

## Output validation and limitations

The forecast grid follows the requested calendar month, including leap years, with 48 half-hour slots per day. Output groups use arbitrary generic labels. The export routine rejects missing/infinite/negative metrics, invalid rates, noninteger abandoned-call counts, inconsistent counts, duplicate keys, incomplete grids and unexpected columns before creating or overwriting the result file.

The method does not model unexpected shocks, production drift or detailed staffing constraints. Ratio extrapolation and a fixed planning bias need independent validation before operational use. The public example schema and dates differ from the confidential submission, so the public output should not be presented as a submission-ready competition file.
