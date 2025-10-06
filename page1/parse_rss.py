# helpers_rss_min.py
from typing import List, Tuple
import pandas as pd
from urllib.parse import urlparse
from .db import fetch_df
from .dates import parse_publish_date_col

import pandas as pd

def rss_as_tuples(limit: int = 50):
    df = fetch_df(f"""
        SELECT TITLE, SUMMARY, SOURCE_NAME, URL, PUBLISHED_AT_RAW
        FROM SNACKLASH2.RAW.RSS_ARTICLES
        LIMIT {int(limit*5)}               -- grab a little extra, we’ll sort+slice
    """)

    # 1) Keep your nice label date
    df["DATE"] = parse_publish_date_col(df["PUBLISHED_AT_RAW"])

    # 2) Add a proper timestamp for sorting (PT shown; keep UTC by dropping tz_convert)
    ts = pd.to_datetime(df["PUBLISHED_AT_RAW"], errors="coerce", utc=True)
    ts = ts.dt.tz_convert("America/Los_Angeles")
    df = (
        df.assign(_TS=ts)
          .sort_values("_TS", ascending=False, na_position="last")
          .head(limit)                     # now take the newest
          .drop(columns="_TS")
    )

    out = []
    for _, r in df.iterrows():
        title   = (r["TITLE"] or "").strip()
        summary = (r["SUMMARY"] or "").strip()
        src     = ((r["SOURCE_NAME"] or "") or "source").strip()
        label   = f"{src} {r['DATE']}" if r["DATE"] else src
        url     = str(r["URL"]) if pd.notna(r["URL"]) else ""
        out.append((title, summary, [(label, url)]))
    return out
