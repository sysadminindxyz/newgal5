# page1/tweet_query.py
from __future__ import annotations
from typing import Dict, Tuple, List

def _clean_terms(kw_raw: str) -> List[str]:
    # split by comma/space, lower-case, drop empties/dupes
    import re
    terms = [t.strip() for t in re.split(r"[,\s]+", kw_raw) if t.strip()]
    # keep order but de-dup
    seen = set(); out=[]
    for t in terms:
        tl = t.lower()
        if tl not in seen:
            seen.add(tl); out.append(t)
    return out

def build_filters_sql(
    start_date, end_date, kw_raw: str, match_mode: str
) -> Tuple[str, Dict[str, str]]:
    """
    Returns (where_sql, params) for safe binding.
    Date inputs are Python date objects.
    """
    where = ["TWEET_URL IS NOT NULL"]
    params: Dict[str, str] = {}

    # dates -> TIMESTAMP_NTZ (inclusive range)
    params["start"] = f"{start_date} 00:00:00"
    params["end"]   = f"{end_date} 23:59:59"
    where.append("CREATED_AT BETWEEN TO_TIMESTAMP_NTZ(:start) AND TO_TIMESTAMP_NTZ(:end)")

    # keywords -> ILIKE with bound params (avoid regex quoting headaches)
    terms = _clean_terms(kw_raw)
    if terms:
        bits = []
        for i, t in enumerate(terms):
            key = f"kw{i}"
            params[key] = f"%{t}%"
            bits.append(f"TWEET_TEXT ILIKE :{key}")
        if match_mode.startswith("Any"):
            where.append("(" + " OR ".join(bits) + ")")
        else:
            where.append("(" + " AND ".join(bits) + ")")

    where_sql = " WHERE " + " AND ".join(where)
    return where_sql, params

def build_order_by(sort_label: str) -> str:
    # stable tie-breaker by extracted status id (descending for recent, ascending otherwise)
    # Using TRY_TO_NUMBER to avoid errors if URL is weird
    tid = "TRY_TO_NUMBER(REGEXP_SUBSTR(TWEET_URL, '/status/(\\d+)'))"
    if sort_label == "Oldest":
        return f" ORDER BY CREATED_AT ASC, {tid} ASC"
    if sort_label == "Title A–Z":
        return f" ORDER BY TWEET_TEXT ASC NULLS LAST, CREATED_AT DESC, {tid} DESC"
    # default: Most recent
    return f" ORDER BY CREATED_AT DESC, {tid} DESC"
