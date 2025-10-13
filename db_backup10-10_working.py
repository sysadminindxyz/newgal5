# db.py
import pandas as pd
import streamlit as st
import snowflake.connector
from cryptography.hazmat.primitives import serialization
import base64
from config import load_config
import math

@st.cache_resource
def get_conn():
    cfg = load_config()
    key = serialization.load_pem_private_key(
        base64.b64decode(cfg["PRIVATE_KEY_PEM_B64"]),
        password=(cfg.get("PRIVATE_KEY_PASSPHRASE") or "").encode() or None,
    ).private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return snowflake.connector.connect(
        account=cfg["SNOWFLAKE_ACCOUNT"],
        user=cfg["SNOWFLAKE_USER"],
        role=cfg["SNOWFLAKE_ROLE"],
        warehouse=cfg["SNOWFLAKE_WAREHOUSE"],
        database=cfg["SNOWFLAKE_DATABASE"],
        schema=cfg["SNOWFLAKE_SCHEMA"],
        private_key=key,
        client_session_keep_alive=True,
    )

@st.cache_data(ttl=300)
def fetch_df(sql: str, params=None) -> pd.DataFrame:
    """
    params can be either a dict or tuple of (key, value) pairs.
    Tuple is preferred for caching purposes.
    """
    import re
    
    # Convert tuple to dict if needed
    if params is None:
        p = {}
    elif isinstance(params, tuple):
        p = dict(params)
    else:
        p = params.copy()

    # Find %(name)s binds in the SQL (pyformat style for Snowflake)
    names = set(re.findall(r"%\(([A-Za-z_][A-Za-z0-9_]*)\)s", sql or ""))

    # Fail fast if anything is missing
    missing = names - set(p.keys())
    if missing:
        raise ValueError(f"Missing bind params {sorted(missing)} for SQL:\n{sql}")

    # Optional: prune extras (params Snowflake won't use)
    for k in list(p.keys()):
        if k not in names:
            p.pop(k, None)

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, p)
        return cur.fetch_pandas_all()
    finally:
        cur.close()


@st.cache_data(ttl=300, show_spinner=False)
def _window_counts(table: str, ts_col: str, where_sql: str = "", params_tuple: tuple = None) -> dict:
    """
    Trailing windows from NOW():
      - day:   last 24h vs previous 24h
      - week:  last 7d  vs previous 7d
      - d28:   last 28d vs previous 28d
    
    params_tuple: tuple of (key, value) pairs for bind parameters
    """
    sql = f"""
    SELECT
      /* 24h windows */
      COALESCE(COUNT_IF({ts_col} >= DATEADD(day, -1, CURRENT_TIMESTAMP()) AND {ts_col} < CURRENT_TIMESTAMP()), 0)                      AS day_curr,
      COALESCE(COUNT_IF({ts_col} >= DATEADD(day, -2, CURRENT_TIMESTAMP()) AND {ts_col} < DATEADD(day, -1, CURRENT_TIMESTAMP())), 0)   AS day_prev,

      /* 7-day windows */
      COALESCE(COUNT_IF({ts_col} >= DATEADD(day, -7, CURRENT_TIMESTAMP()) AND {ts_col} < CURRENT_TIMESTAMP()), 0)                      AS week_curr,
      COALESCE(COUNT_IF({ts_col} >= DATEADD(day, -14, CURRENT_TIMESTAMP()) AND {ts_col} < DATEADD(day, -7, CURRENT_TIMESTAMP())), 0)  AS week_prev,

      /* 28-day windows */
      COALESCE(COUNT_IF({ts_col} >= DATEADD(day, -28, CURRENT_TIMESTAMP()) AND {ts_col} < CURRENT_TIMESTAMP()), 0)                     AS d28_curr,
      COALESCE(COUNT_IF({ts_col} >= DATEADD(day, -56, CURRENT_TIMESTAMP()) AND {ts_col} < DATEADD(day, -28, CURRENT_TIMESTAMP())), 0) AS d28_prev
    FROM {table}
    {f"WHERE {where_sql}" if where_sql else ""}
    """
    df = fetch_df(sql, params_tuple)
    if df.empty:
        return {"day_curr":0,"day_prev":0,"week_curr":0,"week_prev":0,"d28_curr":0,"d28_prev":0}

    row = df.iloc[0].fillna(0).to_dict()

    def _to_int_safe(v):
        try:
            return int(v) if v is not None else 0
        except Exception:
            # handles float('nan') or weird types
            try:
                import math
                return 0 if (isinstance(v, float) and math.isnan(v)) else int(float(v))
            except Exception:
                return 0

    return {k: _to_int_safe(row.get(k)) for k in ["day_curr","day_prev","week_curr","week_prev","d28_curr","d28_prev"]}


def _pct_change(curr: int, prev: int) -> str:
    if prev == 0:
        return "—" if curr == 0 else "+∞%"
    return f"{(curr - prev) / prev * 100.0:+.1f}%"

def summarize_windows(table: str, ts_col: str, where_sql: str = "", params: dict | None = None) -> dict:
    """
    Non-cached wrapper that converts dict to tuple for _window_counts
    """
    params_tuple = tuple(sorted(params.items())) if params else None
    c = _window_counts(table, ts_col, where_sql, params_tuple)
    return {
        "day":  {"count": c["day_curr"],  "delta": _pct_change(c["day_curr"],  c["day_prev"])},
        "week": {"count": c["week_curr"], "delta": _pct_change(c["week_curr"], c["week_prev"])},
        "d28":  {"count": c["d28_curr"],  "delta": _pct_change(c["d28_curr"],  c["d28_prev"])},
    }


@st.cache_data(ttl=120, show_spinner=False)
def summarize_categories_for_filters(where_sql: str, params_tuple: tuple):
    """
    Build the candidate tweet set from MART.TWEET_MEDIA using filters
    (where_sql + params) left list, then compute 7d / 28d
    category counts, their denominators, percents, and avg scores.

    params_tuple: tuple of (key, value) pairs for bind parameters

    Returns columns used by your UI:
      CATEGORY,
      TWEET_COUNT_7D, TWEET_COUNT_7D_PREV,
      PCT_OF_TWEETS_7D,
      TWEET_COUNT_28D, TWEET_COUNT_28D_PREV,
      PCT_OF_TWEETS_28D,
      AVG_SCORE_7D, AVG_SCORE_28D
    """
    sql = f"""
    WITH candidate AS (
      SELECT TWEET_ID, CREATED_AT
      FROM MART.TWEET_MEDIA
      {where_sql}
    ),

    denominators AS (
      SELECT
        COUNT(DISTINCT CASE
          WHEN CREATED_AT >= DATEADD(day,-7,  CURRENT_TIMESTAMP())
           AND CREATED_AT <  CURRENT_TIMESTAMP()
        THEN TWEET_ID END) AS WEEK_TWEETS_CURR,

        COUNT(DISTINCT CASE
          WHEN CREATED_AT >= DATEADD(day,-14, CURRENT_TIMESTAMP())
           AND CREATED_AT <  DATEADD(day,-7,  CURRENT_TIMESTAMP())
        THEN TWEET_ID END) AS WEEK_TWEETS_PREV,

        COUNT(DISTINCT CASE
          WHEN CREATED_AT >= DATEADD(day,-28, CURRENT_TIMESTAMP())
           AND CREATED_AT <  CURRENT_TIMESTAMP()
        THEN TWEET_ID END) AS D28_TWEETS_CURR,

        COUNT(DISTINCT CASE
          WHEN CREATED_AT >= DATEADD(day,-56, CURRENT_TIMESTAMP())
           AND CREATED_AT <  DATEADD(day,-28, CURRENT_TIMESTAMP())
        THEN TWEET_ID END) AS D28_TWEETS_PREV
      FROM candidate
    ),

    category_map AS (
      -- distinct (tweet, category, score) among the filtered candidates
      SELECT DISTINCT
        candidate.TWEET_ID,
        MART.TWEET_AI_CATEGORIES_FLAT.CATEGORY,
        MART.TWEET_AI_CATEGORIES_FLAT.SCORE
      FROM candidate
      JOIN MART.TWEET_AI_CATEGORIES_FLAT
        ON MART.TWEET_AI_CATEGORIES_FLAT.TWEET_ID = candidate.TWEET_ID
    ),

    aggregate_by_category AS (
      SELECT
        category_map.CATEGORY,

        COUNT(DISTINCT CASE
          WHEN candidate.CREATED_AT >= DATEADD(day,-7,  CURRENT_TIMESTAMP())
           AND candidate.CREATED_AT <  CURRENT_TIMESTAMP()
        THEN candidate.TWEET_ID END) AS TWEET_COUNT_7D,

        COUNT(DISTINCT CASE
          WHEN candidate.CREATED_AT >= DATEADD(day,-14, CURRENT_TIMESTAMP())
           AND candidate.CREATED_AT <  DATEADD(day,-7,  CURRENT_TIMESTAMP())
        THEN candidate.TWEET_ID END) AS TWEET_COUNT_7D_PREV,

        COUNT(DISTINCT CASE
          WHEN candidate.CREATED_AT >= DATEADD(day,-28, CURRENT_TIMESTAMP())
           AND candidate.CREATED_AT <  CURRENT_TIMESTAMP()
        THEN candidate.TWEET_ID END) AS TWEET_COUNT_28D,

        COUNT(DISTINCT CASE
          WHEN candidate.CREATED_AT >= DATEADD(day,-56, CURRENT_TIMESTAMP())
           AND candidate.CREATED_AT <  DATEADD(day,-28, CURRENT_TIMESTAMP())
        THEN candidate.TWEET_ID END) AS TWEET_COUNT_28D_PREV,

        AVG(CASE
          WHEN candidate.CREATED_AT >= DATEADD(day,-7,  CURRENT_TIMESTAMP())
           AND candidate.CREATED_AT <  CURRENT_TIMESTAMP()
        THEN category_map.SCORE END) AS AVG_SCORE_7D,

        AVG(CASE
          WHEN candidate.CREATED_AT >= DATEADD(day,-28, CURRENT_TIMESTAMP())
           AND candidate.CREATED_AT <  CURRENT_TIMESTAMP()
        THEN category_map.SCORE END) AS AVG_SCORE_28D

      FROM category_map
      JOIN candidate ON candidate.TWEET_ID = category_map.TWEET_ID
      GROUP BY category_map.CATEGORY
    )

    SELECT
      aggregate_by_category.CATEGORY,

      aggregate_by_category.TWEET_COUNT_7D,
      IFF(denominators.WEEK_TWEETS_CURR = 0, NULL,
          aggregate_by_category.TWEET_COUNT_7D * 100.0 / denominators.WEEK_TWEETS_CURR
      ) AS PCT_OF_TWEETS_7D,

      aggregate_by_category.TWEET_COUNT_7D_PREV,

      aggregate_by_category.TWEET_COUNT_28D,
      IFF(denominators.D28_TWEETS_CURR = 0, NULL,
          aggregate_by_category.TWEET_COUNT_28D * 100.0 / denominators.D28_TWEETS_CURR
      ) AS PCT_OF_TWEETS_28D,

      aggregate_by_category.TWEET_COUNT_28D_PREV,

      aggregate_by_category.AVG_SCORE_7D,
      aggregate_by_category.AVG_SCORE_28D

    FROM aggregate_by_category
    CROSS JOIN denominators
    ORDER BY aggregate_by_category.TWEET_COUNT_28D DESC,
             aggregate_by_category.TWEET_COUNT_7D  DESC,
             aggregate_by_category.CATEGORY;
    """
    return fetch_df(sql, params_tuple)