# helpers_rss_min.py
from typing import List, Tuple
from urllib.parse import urlparse
import pandas as pd
from db import fetch_df

def rss_as_tuples(limit: int = 50) -> List[Tuple[str, str, list]]:
    df = fetch_df(f"""
        SELECT TITLE, SUMMARY, SOURCE_NAME, URL, PUBLISHED_AT_RAW
        FROM SNACKLASH2.RAW.RSS_ARTICLES
        ORDER BY PUBLISHED_AT_RAW DESC
        LIMIT {int(limit)}
    """)

    # Parse date → MM/DD/YYYY (keeps leading zeros; reliable cross-platform)
    dt = pd.to_datetime(df["PUBLISHED_AT_RAW"], errors="coerce", utc=False)
    date_str = dt.dt.strftime("%m/%d/%Y")

    out = []
    for i, row in df.assign(DATE=date_str).iterrows():
        title   = (row["TITLE"] or "").strip()
        summary = (row["SUMMARY"] or "").strip()

        # Source label (fallback to hostname if SOURCE_NAME missing)
        src = (row["SOURCE_NAME"] or "").strip()
        if not src:
            try:
                src = (urlparse(row["URL"]).hostname or "source").replace("www.", "")
            except Exception:
                src = "source"

        label = f"{src} {row['DATE']}" if row["DATE"] else src
        url   = str(row["URL"]) if pd.notna(row["URL"]) else ""

        out.append((title, summary, [(label, url)]))
    return out