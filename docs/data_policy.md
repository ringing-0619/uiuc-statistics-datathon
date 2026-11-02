# Data policy and public example schema

No original competition records, observed aggregate findings, trained weights, fitted profiles, tracking stores or submitted predictions are included. The synthetic generator uses arbitrary constants and a reproducible random seed. It does not read private files or derive parameters from private summaries.

## Public example interface

The optional workbook has two sheets for each generic label in `src/config.py`: `group_1_daily` and `group_1_interval`, and the corresponding sheets for the other demo groups. These are example labels, not a mapping of confidential business groups.

| Sheet kind | Required columns | Meaning |
| --- | --- | --- |
| daily | `Date`, `CV`, `CCT`, `ABD` | Calendar date, daily volume, care-time level, abandon rate |
| interval | `Date`, `Interval`, `CV`, `CCT`, `ABD` | Calendar date, half-hour time, interval volume, care-time level, abandon rate |

Dates must be timezone-naive calendar dates, supplied as ISO date text or Excel date cells. Intervals accept `HH:MM`, `HH:MM:SS`, Excel time cells or fractional Excel days and must align to half hours. Rates are fractions in `[0, 1]`; all metrics must be finite and nonnegative. Duplicate daily dates or interval date/time keys are rejected. Invalid times are rejected instead of being silently dropped.

No staffing sheet, original filename, competition sheet layout or official submission template is needed. A private source workbook must be adapted locally to this generic interface; no competition adapter is distributed. The demonstration needs two complete historical years and interval examples before the forecast month. Optional backtests need complete historical validation months.

## Running with confidential inputs

Only the path explicitly supplied with `--data` is opened. There is no automatic directory search, private dataset default, remote tracking client or environment-driven upload. Generic progress messages do not include observed values or input previews. Forecasts are written locally, and a `--data` run is treated as private regardless of its filename.

Keep real inputs, generated predictions, manually inspected metrics and model/profile artifacts out of public Git commits, issues, screenshots, notebooks, CI logs and shared archives unless disclosure is explicitly authorized. Removing direct identifiers, changing group names or deleting the original spreadsheet does not make derived statistics automatically public.

All `data/` and `outputs/` files, databases, logs, serialized models, credentials and caches are ignored. Existing tracked files and Git history require separate review: `.gitignore` does not erase prior commits. The public repository starts with the sanitized source; no private Git history is carried over.

## Disclosure boundaries

Technical cleaning cannot establish permission to publish team code or competition-specific intellectual property. Confirm the organizer's terms and appropriate attribution before publication. No specific team member's contribution, competition rank or measured business result is asserted here.
