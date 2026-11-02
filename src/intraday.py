"""
Intraday profile builder.

For each portfolio and each day-of-week (0-6), computes the expected
share of daily call volume arriving in each 30-minute slot.

    share[dow][slot] = E[ CV_slot / CV_daily ]

These shares are used to distribute daily CV forecasts into 48 per-slot values.

Profiles are estimated at runtime. No confidential exploratory findings,
observed peak times or business-specific proportions are embedded here.
"""
import numpy as np
import pandas as pd

from config import PORTFOLIOS, SLOTS_PER_DAY


# Generic half-hour grid used by the public demonstration.
SLOT_LABELS = [
    f"{h}:{m:02d}" for h in range(24) for m in (0, 30)
]   # ['0:00','0:30','1:00',...,'23:30']


def _slot_key(hour: float) -> str:
    """Convert fractional hour → canonical slot string."""
    h = int(hour)
    m = 30 if (hour % 1) >= 0.5 else 0
    return f"{h}:{m:02d}"


def build_cv_profile(interval_df: pd.DataFrame) -> dict:
    """
    Build per-DOW CV share profiles from the interval data.

    Returns
    -------
    profile : dict[dow (0-6)] → np.ndarray shape (48,)
              Values represent E[fraction of day's CV in each slot].
              Rows (slot order) follow SLOT_LABELS.
    """
    df = interval_df.copy()
    df = df.dropna(subset=["CV", "hour"])

    # Compute each day's total CV
    daily_totals = (
        df.groupby(["Date"])["CV"]
        .sum()
        .rename("daily_total")
        .reset_index()
    )
    df = df.merge(daily_totals, on="Date", how="left")

    # Drop days with zero total (edge case — would give 0/0)
    df = df[df["daily_total"] > 0].copy()
    if df.empty:
        raise ValueError("A volume profile requires positive interval call totals.")
    df["share"] = df["CV"] / df["daily_total"]
    df["slot_str"] = df["hour"].apply(_slot_key)

    profile = {}
    for dow in range(7):
        sub = df[df["DOW"] == dow]
        if len(sub) == 0:
            # Fallback: use weekday or weekend average
            fallback_group = list(range(5)) if dow < 5 else [5, 6]
            sub = df[df["DOW"].isin(fallback_group)]
        if sub.empty:
            sub = df

        # Mean share per slot across all days of this DOW
        slot_avg = (
            sub.groupby("slot_str")["share"]
            .mean()
            .reindex(SLOT_LABELS, fill_value=0.0)
        )

        # Re-normalise to guarantee sum = 1 (handles missing overnight slots)
        total = slot_avg.sum()
        if total > 0:
            slot_avg = slot_avg / total

        profile[dow] = slot_avg.values   # shape (48,)

    return profile


def build_cct_profile(interval_df: pd.DataFrame) -> dict:
    """
    Build per-DOW CCT intraday profiles.

    CCT is NOT a share; it is the average handle-time value at each slot.
    Returns dict[dow] → np.ndarray(48,)  of mean CCT in seconds.
    """
    df = interval_df.dropna(subset=["CCT", "hour"]).copy()
    if df.empty:
        raise ValueError("A care-time profile requires finite interval observations.")
    df["slot_str"] = df["hour"].apply(_slot_key)

    profile = {}
    for dow in range(7):
        sub = df[df["DOW"] == dow]
        if len(sub) == 0:
            fallback = list(range(5)) if dow < 5 else [5, 6]
            sub = df[df["DOW"].isin(fallback)]
        if sub.empty:
            sub = df

        slot_cct = (
            sub.groupby("slot_str")["CCT"]
            .mean()
            .reindex(SLOT_LABELS, fill_value=np.nan)
        )
        # Forward-fill then backward-fill any NaN slots
        slot_cct = slot_cct.ffill().bfill()
        profile[dow] = slot_cct.values

    return profile


def build_abd_profile(interval_df: pd.DataFrame) -> dict:
    """
    Build per-DOW Abandoned Rate intraday profiles.

    Returns dict[dow] → np.ndarray(48,)  of mean ABD rate [0, 1].
    """
    df = interval_df.dropna(subset=["ABD", "hour"]).copy()
    if df.empty:
        raise ValueError("An abandon-rate profile requires finite interval observations.")
    df["slot_str"] = df["hour"].apply(_slot_key)

    profile = {}
    for dow in range(7):
        sub = df[df["DOW"] == dow]
        if len(sub) == 0:
            fallback = list(range(5)) if dow < 5 else [5, 6]
            sub = df[df["DOW"].isin(fallback)]
        if sub.empty:
            sub = df

        slot_abd = (
            sub.groupby("slot_str")["ABD"]
            .mean()
            .reindex(SLOT_LABELS, fill_value=np.nan)
        )
        slot_abd = slot_abd.ffill().bfill().clip(0, 1)
        profile[dow] = slot_abd.values

    return profile


def build_all_profiles(interval: dict) -> dict:
    """
    Build CV / CCT / ABD profiles for all portfolios.

    Returns
    -------
    profiles : dict[portfolio] → {
        'cv'  : dict[dow] → ndarray(48),
        'cct' : dict[dow] → ndarray(48),
        'abd' : dict[dow] → ndarray(48),
    }
    """
    profiles = {}
    for p in PORTFOLIOS:
        df = interval[p]
        profiles[p] = {
            "cv" : build_cv_profile(df),
            "cct": build_cct_profile(df),
            "abd": build_abd_profile(df),
        }
        # Check validity without printing observed business statistics.
        for dow in range(7):
            s = profiles[p]["cv"][dow].sum()
            if not np.isfinite(s) or abs(s - 1.0) >= 1e-6:
                raise ValueError("An interval volume profile is not normalized.")
            for metric in ("cct", "abd"):
                if not np.isfinite(profiles[p][metric][dow]).all():
                    raise ValueError("An interval profile contains invalid values.")

    return profiles
