# dates.py
import pandas as pd
import numpy as np

TZ = "America/Los_Angeles"  # change to None to keep UTC day

def parse_publish_date_col(s: pd.Series) -> pd.Series:
    # normalize empties to NaN
    s = s.astype("string").str.strip().replace({"": np.nan, "None": np.nan, "nan": np.nan, "NaN": np.nan})

    # fast/strict pass for RFC-2822 like "Wed, 24 Sep 2025 14:17:29 GMT"
    d_utc = pd.to_datetime(s, format="%a, %d %b %Y %H:%M:%S %Z", errors="coerce", utc=True)

    # fallback pass for anything that didn't match exactly (ISO, oddball feeds, etc.)
    mask = d_utc.isna()
    if mask.any():
        d_utc.loc[mask] = pd.to_datetime(s[mask], errors="coerce", utc=True)

    # convert to local tz (so the calendar date matches PT) then format
    if TZ:
        d_local = d_utc.dt.tz_convert(TZ)
    else:
        d_local = d_utc  # stays UTC

    return d_local.dt.strftime("%m/%d/%Y")  # portable on all OS; keeps leading zeros
