# page2_twitter.py
import re, json
import streamlit as st
from streamlit.components.v1 import html as html_component
from db import fetch_df  
import datetime as dt
from db import summarize_categories_for_filters
import pandas as pd

_ID_RE = re.compile(r"(?:status/|status%2F|i/web/status/)(\d+)")
def _extract_id(u: str) -> str | None:
    m = _ID_RE.search(str(u).strip())
    return m.group(1) if m else None


# --- helpers ---------------------------------------------------------------

def _normalize(u: str) -> str:
    # x.com → twitter.com is more reliable for widgets.js
    return re.sub(r"^https?://x\.com/", "https://twitter.com/", u.strip())

@st.cache_data(ttl=600, show_spinner=False)
def _total_tweet_count() -> int:
    df = fetch_df("""
        SELECT COUNT(*) AS N
        FROM MART.TWEET_MEDIA
        WHERE TWEET_URL IS NOT NULL
    """)
    return int(df["N"].iloc[0])
@st.cache_data(ttl=120, show_spinner=False)
def _count_filtered(where_sql: str, params_tuple: tuple) -> int:
    params = dict(params_tuple) if params_tuple else {}
    _assert_all_bind_params(where_sql, params)
    # ✅ Just pass params_tuple directly - don't recreate it!
    df = fetch_df(f"SELECT COUNT(*) AS N FROM MART.TWEET_MEDIA {where_sql}", params_tuple)
    return int(df["N"].iat[0])

@st.cache_data(ttl=60, show_spinner=False)
def _get_urls_filtered(where_sql: str, order_sql: str, params_tuple: tuple, limit: int, offset: int) -> list[str]:
    params = dict(params_tuple) if params_tuple else {}
    _assert_all_bind_params(where_sql, params)
    sql = f"""
      SELECT TWEET_URL
      FROM MART.TWEET_MEDIA
      {where_sql}
      {order_sql}
      LIMIT {int(limit)} OFFSET {int(offset)}
    """
    # ✅ Just pass params_tuple directly - don't recreate it!
    df = fetch_df(sql, params_tuple)
    return [_normalize(str(u)) for u in df["TWEET_URL"].dropna().astype(str)]

def _render_embeds(urls: list[str], theme: str = "dark") -> None:
    """
    Programmatically embed by Tweet ID so /i/web/status/... works.
    Fixed width, dynamic height per tweet. Shows as many as resolve.
    """
    # ✅ build ids from the URLs (this was missing)
    ids = [tid for tid in (_extract_id(u) for u in urls) if tid]
    if not ids:
        html_component("<div style='color:#999'>No embeddable tweets.</div>", height=60)
        return
    containers = "\n".join(
        f'<div id="t-{tid}" style="margin:0 0 12px 0;"></div>' for tid in ids
    )
    html = f"""
    <!doctype html><meta charset="utf-8"/>
    <style>
      html,body {{ margin:0; background:#fff; }}
      #wrap      {{ width:650px; max-width:100%; margin:0 auto; }}
      blockquote.twitter-tweet {{ margin: 0 0 12px 0 !important; }}
    </style>
    <div id="wrap">{containers}</div>
    <script>
      const IDS = {json.dumps(ids)};
      function boot() {{
        if (!window.twttr || !twttr.widgets || !twttr.widgets.createTweet) {{
          return setTimeout(boot, 60);
        }}
        for (const id of IDS) {{
          const el = document.getElementById("t-" + id);
          if (!el) continue;
          twttr.widgets.createTweet(id, el, {{
            theme: {json.dumps(theme)},
            conversation: "none",
            align: "center"
          }});
        }}
      }}
      window.addEventListener("load", boot);
    </script>
    <script async src="https://platform.twitter.com/widgets.js"></script>
    """
    # tight height so controls sit close; tweak per if needed
    per = 560 if theme == "dark" else 520
    min_h, max_h = 600, 2400
    height = max(min_h, min(120 + per * len(ids), max_h))
    html_component(html, height=height, scrolling=True)

# --- filter SQL builders ----------------------------------------------------
# --- filters (no category) -------------------------------------------------

def _clean_terms(kw_raw: str) -> list[str]:
    import re
    if not kw_raw:
        return []
    terms = [t.strip() for t in re.split(r"[,\s]+", str(kw_raw)) if t.strip()]
    out, seen = [], set()
    for t in terms:
        k = t.lower()
        if k not in seen:
            seen.add(k); out.append(t)
    return out

def _build_filters_sql(start_date, end_date, kw_raw: str, match_mode: str, use_date: bool):
    clauses = ["TWEET_URL IS NOT NULL"]
    params = {}

    if use_date:
        params["start"] = f"{start_date} 00:00:00"
        params["end"]   = f"{end_date} 23:59:59"
        clauses.append("CREATED_AT BETWEEN TO_TIMESTAMP_NTZ(%(start)s) AND TO_TIMESTAMP_NTZ(%(end)s)")

    terms = _clean_terms(kw_raw)
    if terms:
        bits = []
        for i, t in enumerate(terms):
            k = f"kw{i}"
            params[k] = f"%{t}%"
            bits.append(f"TWEET_TEXT ILIKE %({k})s")  # ← Changed from :kw0 to %(kw0)s
        op = " OR " if str(match_mode).lower().startswith("any") else " AND "
        clauses.append("(" + op.join(bits) + ")")

    where_sql = " WHERE " + " AND ".join(clauses)
    return where_sql, params

def _build_order_by(sort_label: str) -> str:
    tid = "TRY_TO_NUMBER(REGEXP_SUBSTR(TWEET_URL, '/status/(\\d+)'))"
    if sort_label == "Oldest":
        return f" ORDER BY CREATED_AT ASC, {tid} ASC"
    if sort_label == "Title A–Z":
        return f" ORDER BY TWEET_TEXT ASC NULLS LAST, CREATED_AT DESC, {tid} DESC"
    return f" ORDER BY CREATED_AT DESC, {tid} DESC"

def _assert_all_bind_params(where_sql: str, params: dict):
    import re
    needed = set(re.findall(r":([A-Za-z_][A-Za-z0-9_]*)", where_sql or ""))
    missing = needed - set((params or {}).keys())
    if missing:
        raise ValueError(f"Missing bind params for {sorted(missing)} in WHERE: {where_sql}")

def _assert_all_binds_present(sql: str, params: dict):
    needed = re.findall(r":([A-Za-z_]\w*)", sql)
    missing = [k for k in needed if k not in (params or {})]
    if missing:
        raise ValueError(f"Missing binds {missing} for SQL:\n{sql}")

@st.cache_data(ttl=120, show_spinner=False)
def _category_summary_windows_flat(
    kw_raw: str,
    match_mode: str,
    summaries_use_date: bool,
    start_date,  # date
    end_date,    # date
) -> "pd.DataFrame":
    """
    Summarize categories for the set of tweet_ids that match the *text* filter.
    Text lives in STAGE.TWEETS__CLEAN_WITH_AUTHORS; categories live in MART.TWEET_AI_CATEGORIES_FLAT.
    Time windows are computed on the categories' CREATED_AT.
    """
    terms = _clean_terms(kw_raw)
    params = {}

    # --- keyword WHERE against tweet text (in STAGE) ---
    text_bits = []
    if terms:
        if match_mode.startswith("Any"):
            ors = []
            for i, t in enumerate(terms):
                k = f"kw{i}"; params[k] = f"%{t}%"
                ors.append(f"(s.TEXT_CLEAN_SUB ILIKE :{k} OR s.TEXT ILIKE :{k})")
            text_bits.append("(" + " OR ".join(ors) + ")")
        else:
            for i, t in enumerate(terms):
                k = f"kw{i}"; params[k] = f"%{t}%"
                text_bits.append(f"(s.TEXT_CLEAN_SUB ILIKE :{k} OR s.TEXT ILIKE :{k})")

    text_where = ("WHERE " + " AND ".join(text_bits)) if text_bits else ""

    # If you want the *summary* to obey the sidebar date range, apply it here
    # (on categories CREATED_AT). Otherwise, leave these NULL and we’ll use trailing windows.
    if summaries_use_date and start_date and end_date:
        params["d_start"] = f"{start_date} 00:00:00"
        params["d_end"]   = f"{end_date} 23:59:59"
        date_filter = "AND c.CREATED_AT BETWEEN TO_TIMESTAMP_NTZ(:d_start) AND TO_TIMESTAMP_NTZ(:d_end)"
    else:
        date_filter = ""  # trailing windows only

    sql = f"""
    WITH eligible AS (
      SELECT DISTINCT m.TWEET_ID
      FROM MART.TWEET_MEDIA m
      LEFT JOIN STAGE.TWEETS__CLEAN_WITH_AUTHORS s USING (TWEET_ID)
      {text_where}
    ),
    joined AS (
      SELECT c.TWEET_ID, c.CATEGORY, c.SCORE, c.CREATED_AT
      FROM MART.TWEET_AI_CATEGORIES_FLAT c
      JOIN eligible e ON e.TWEET_ID = c.TWEET_ID
      WHERE c.CATEGORY IS NOT NULL
      {date_filter}
    ),
    totals AS (
      SELECT
        COUNT(DISTINCT CASE WHEN CREATED_AT >= DATEADD(day,-7,CURRENT_TIMESTAMP())
                              AND CREATED_AT <  CURRENT_TIMESTAMP() THEN TWEET_ID END) AS total_7d,
        COUNT(DISTINCT CASE WHEN CREATED_AT >= DATEADD(day,-14,CURRENT_TIMESTAMP())
                              AND CREATED_AT <  DATEADD(day,-7,CURRENT_TIMESTAMP()) THEN TWEET_ID END) AS total_7d_prev,
        COUNT(DISTINCT CASE WHEN CREATED_AT >= DATEADD(day,-28,CURRENT_TIMESTAMP())
                              AND CREATED_AT <  CURRENT_TIMESTAMP() THEN TWEET_ID END) AS total_28d,
        COUNT(DISTINCT CASE WHEN CREATED_AT >= DATEADD(day,-56,CURRENT_TIMESTAMP())
                              AND CREATED_AT <  DATEADD(day,-28,CURRENT_TIMESTAMP()) THEN TWEET_ID END) AS total_28d_prev
      FROM joined
    )
    SELECT
      CATEGORY,
      COUNT(DISTINCT CASE WHEN j.CREATED_AT >= DATEADD(day,-7,CURRENT_TIMESTAMP())
                            AND j.CREATED_AT <  CURRENT_TIMESTAMP() THEN j.TWEET_ID END) AS tweet_count_7d,
      COUNT(DISTINCT CASE WHEN j.CREATED_AT >= DATEADD(day,-14,CURRENT_TIMESTAMP())
                            AND j.CREATED_AT <  DATEADD(day,-7,CURRENT_TIMESTAMP()) THEN j.TWEET_ID END) AS tweet_count_7d_prev,
      COUNT(DISTINCT CASE WHEN j.CREATED_AT >= DATEADD(day,-28,CURRENT_TIMESTAMP())
                            AND j.CREATED_AT <  CURRENT_TIMESTAMP() THEN j.TWEET_ID END) AS tweet_count_28d,
      COUNT(DISTINCT CASE WHEN j.CREATED_AT >= DATEADD(day,-56,CURRENT_TIMESTAMP())
                            AND j.CREATED_AT <  DATEADD(day,-28,CURRENT_TIMESTAMP()) THEN j.TWEET_ID END) AS tweet_count_28d_prev,
      AVG(CASE WHEN j.CREATED_AT >= DATEADD(day,-7,CURRENT_TIMESTAMP())
                 AND j.CREATED_AT <  CURRENT_TIMESTAMP() THEN j.SCORE END) AS avg_score_7d,
      AVG(CASE WHEN j.CREATED_AT >= DATEADD(day,-28,CURRENT_TIMESTAMP())
                 AND j.CREATED_AT <  CURRENT_TIMESTAMP() THEN j.SCORE END) AS avg_score_28d,
      (SELECT total_7d      FROM totals) AS total_7d,
      (SELECT total_7d_prev FROM totals) AS total_7d_prev,
      (SELECT total_28d     FROM totals) AS total_28d,
      (SELECT total_28d_prev FROM totals) AS total_28d_prev
    FROM joined j
    GROUP BY CATEGORY
    ORDER BY CATEGORY
    """
    df = fetch_df(sql, params)

    if df.empty:
        return df

    # percents (of tweets in that window)
    for window in ("7d", "28d"):
        denom_col = f"TOTAL_{window.upper()}"
        num_col   = f"TWEET_COUNT_{window.upper()}"
        if denom_col in df and num_col in df:
            # Avoid division by zero
            df[f"PCT_OF_TWEETS_{window.upper()}"] = (
                (df[num_col] / df[denom_col].replace(0, pd.NA)) * 100.0
            )

    return df



# --- page UI ---------------------------------------------------------------

def main():
    # #TEMPORARY DEBUG: 
    #st.cache_data.clear()
    # if st.button("🔄 Clear Cache (Debug)", type="secondary"):
    #     st.cache_data.clear()
    #     st.rerun()

    st.set_page_config(layout="wide")
    st.subheader("Trending Social Posts")
    theme= "dark"
    #mode_append = False # append on next vs paginate

    # ---- run-on-rerun hook: clear filters before widgets are created ----
    if st.session_state.pop("__tweet_do_clear", False):
        # drop widget-backed keys so widgets fall back to defaults
        for k in [
            "tweet_use_date",
            "tweet_date_range",
            "tweet_kw",
            "tweet_match_mode",
            "tweet_sort",
            "tweet_page_size_sidebar",
            "tweet_mode_append",
        ]:
            st.session_state.pop(k, None)
        # reset paging/accumulator
        st.session_state["tweet_offset"] = 0
        st.session_state["tweet_accum_urls"] = []

    with st.sidebar:
        if st.button("🔄 Clear All Cache"):
            st.cache_data.clear()
            st.rerun()

        if st.button("Clear filters", type="secondary"):
            st.session_state["__tweet_do_clear"] = True
            st.rerun()

        st.subheader("Filters")

        today = dt.date.today()
        start_default = today - dt.timedelta(days=30)

        use_date = st.checkbox(
            "Filter by date range",
            key="tweet_use_date",
            # ❌ Remove: value=st.session_state.get("tweet_use_date", False),
        )

        if use_date:
            date_range = st.date_input(
                "Date range",
                key="tweet_date_range",
                value=(start_default, today),  # ✅ OK to keep this - it's a default, not session state
                format="MM/DD/YYYY",
            )
            if isinstance(date_range, tuple):
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range
        else:
            start_date = end_date = None

        kw_raw = st.text_input(
            "Keywords (comma/space separated)",
            key="tweet_kw",
            # ❌ Remove: value=st.session_state.get("tweet_kw", ""),
        )

        match_mode = st.radio(
            "Match terms",
            ["Any (OR)", "All (AND)"],
            index=0,
            key="tweet_match_mode",
            horizontal=True,
        )

        sort_label = st.selectbox(
            "Sort by",
            ["Most recent", "Oldest", "Title A–Z"],
            index=0,
            key="tweet_sort",
        )

        page_size = st.selectbox(
            "Page size",
            [5, 10, 15],
            index=1,
            key="tweet_page_size_sidebar",
        )

        mode_append = st.toggle(
            "Append mode (infinite scroll)",
            value=False,  # ✅ This is OK - it's a default
            key="tweet_mode_append",
            help="Keep loading more below instead of paginating.",
        )
        summaries_use_date = st.toggle(
            "Summaries use date filter",
            value=False,
            help="If on, the right-side summaries use the page’s date range instead of fixed last 7/28 days."
        )

        ###TO DEBUG CATEGORY FILTERS
        # # Pull category list once (cached)
        # @st.cache_data(ttl=600, show_spinner=False)
        # def _all_categories() -> list[str]:
        #     df = fetch_df("SELECT DISTINCT CATEGORY FROM MART.TWEET_AI_CATEGORIES_FLAT ORDER BY 1")
        #     return [c for c in df["CATEGORY"].dropna().astype(str)]

        # cat_options = _all_categories()
        # sel_categories = st.multiselect("Categories", options=cat_options, default=[])
        # cat_match_mode = st.radio("Match categories", ["Any (OR)", "All (AND)"], index=0, horizontal=True)

    ###TO DEBUG CATEGORY FILTERS
    # cat_sig = tuple(sorted(sel_categories))  # lists aren’t hashable

    _sig = (
        st.session_state.get("tweet_use_date"),
        start_date, end_date,
        st.session_state.get("tweet_kw"),
        st.session_state.get("tweet_match_mode"),
        st.session_state.get("tweet_sort"),
        st.session_state.get("tweet_page_size_sidebar"),
        st.session_state.get("tweet_mode_append"),
        # cat_sig,                             # ← categories selected
        #cat_match_mode,                      # ← AND/OR
    )

    if st.session_state.get("_tweet_filter_sig") != _sig:
        st.session_state["_tweet_filter_sig"] = _sig
        st.session_state["tweet_offset"] = 0
        st.session_state["tweet_accum_urls"] = []





        
    # Build WHERE + params 
    where_sql, params = _build_filters_sql(start_date, end_date, kw_raw, match_mode, use_date)
    order_sql = _build_order_by(sort_label)
    params_tuple = tuple(sorted(params.items()))
    
    # DEBUG
    # st.write("🔍 DEBUG INFO:")
    # st.write(f"kw_raw = {repr(kw_raw)}")
    # st.write(f"where_sql = {where_sql}")
    # st.write(f"params dict = {params}")
    # st.write(f"params_tuple = {params_tuple}")
    # st.write("---")

    total = _count_filtered(where_sql, params_tuple)
    offset = st.session_state.get("tweet_offset", 0)
    urls = _get_urls_filtered(where_sql, order_sql, params_tuple, page_size, offset)
    max_page = max(1, (total + page_size - 1) // page_size)


    # Labels / summary
    date_label = f"{start_date} → {end_date}" if use_date else "all time"
    total_all = _total_tweet_count()
    st.markdown(f"<div style='margin-top:16px;color:#888'>Total in DB: {total_all:,}</div>", unsafe_allow_html=True)
    st.caption(
        f"{total:,} tweets • {date_label} • {sort_label} • "
        f"{'any' if match_mode.startswith('Any') else 'all'} of: {kw_raw or '—'}"
    )


    # Session state for pagination/append
    if "tweet_offset" not in st.session_state:
        st.session_state.tweet_offset = 0
    if "tweet_accum_urls" not in st.session_state:
        st.session_state.tweet_accum_urls = []

    left, right = st.columns([3, 2], gap="large")  # wider left for tweets


    with left:

        # Nav buttons
        nav1, nav2, nav3 = st.columns([1,1,3])
        with nav1:
            disabled_prev = st.session_state.tweet_offset <= 0
            if st.button("◀ Prev", disabled=disabled_prev):
                st.session_state.tweet_offset = max(0, st.session_state.tweet_offset - page_size)
                if not mode_append:
                    st.session_state.tweet_accum_urls = []
                st.rerun()
        with nav2:
            disabled_next = (st.session_state.tweet_offset + page_size) >= total
            if st.button("Next ▶", disabled=disabled_next):
                if mode_append:
                    # keep current offset for next slice and accumulate
                    pass
                else:
                    st.session_state.tweet_accum_urls = []
                st.session_state.tweet_offset = min(total, st.session_state.tweet_offset + page_size)
                st.rerun()
        with nav3:
            max_page = max(1, (total + page_size - 1) // page_size)
            cur_page = st.number_input(
                "Jump to page", min_value=1, max_value=max_page,
                value=(st.session_state.tweet_offset // page_size) + 1, step=1
            )
            if cur_page != (st.session_state.tweet_offset // page_size) + 1:
                st.session_state.tweet_offset = (int(cur_page) - 1) * page_size
                if not mode_append:
                    st.session_state.tweet_accum_urls = []
                st.rerun()

        cur_urls = _get_urls_filtered(
            where_sql, order_sql, params_tuple,
            limit=page_size*2, offset=st.session_state.tweet_offset
        )

        # Append vs paginate
        if mode_append:
            # Accumulate (dedupe while preserving order)
            seen = set(st.session_state.tweet_accum_urls)
            for u in cur_urls:
                if u not in seen:
                    st.session_state.tweet_accum_urls.append(u); seen.add(u)
            urls_to_render = st.session_state.tweet_accum_urls
        else:
            urls_to_render = cur_urls


        st.caption(f"Showing {len(urls_to_render)} tweet(s) "
                f"[page size {page_size}, offset {st.session_state.tweet_offset}]")

        # Render embeds
        if urls_to_render:
            _render_embeds(urls_to_render, theme=theme)
        else:
            st.info("No tweets to show.")

        # mode_append = False
        # --- bottom pager ---
        st.divider()
        b1, b2, b3 = st.columns([1, 1, 3])

        # (Re)compute current/limits
        max_page = max(1, (total + page_size - 1) // page_size)
        cur_page_val = (st.session_state.tweet_offset // page_size) + 1

        with b1:
            disabled_prev = st.session_state.tweet_offset <= 0
            if st.button("◀ Prev", key="prev_bottom", disabled=disabled_prev):
                st.session_state.tweet_offset = max(0, st.session_state.tweet_offset - page_size)
                if not mode_append:
                    st.session_state.tweet_accum_urls = []
                st.rerun()

        with b2:
            disabled_next = (st.session_state.tweet_offset + page_size) >= total
            if st.button("Next ▶", key="next_bottom", disabled=disabled_next):
                if not mode_append:
                    st.session_state.tweet_accum_urls = []
                st.session_state.tweet_offset = min(total, st.session_state.tweet_offset + page_size)
                st.rerun()

        with b3:
            new_page = st.number_input(
                "Jump to page",
                min_value=1,
                max_value=max_page,
                value=cur_page_val,
                step=1,
                key="tweet_jump_bottom",  # <-- different key from the top control
            )
            if new_page != cur_page_val:
                st.session_state.tweet_offset = (int(new_page) - 1) * page_size
                if not mode_append:
                    st.session_state.tweet_accum_urls = []
                st.rerun()
 
    with right:
        title = "(Date filter on)" if summaries_use_date else "7 & 28 day"
        st.subheader(title)

        try:
            df_sum = summarize_categories_for_filters(where_sql, params_tuple)
        except Exception as e:
            st.error(f"Summary query failed: {e}")
            df_sum = None

        if df_sum is None or df_sum.empty:
            st.info("No category data for the current filters/time window.")
        else:
            # percent changes (safe division)
            import numpy as np
            def pct_change(curr, prev):
                return np.where(prev==0, np.nan, 100.0*(curr - prev)/prev)

            df = df_sum.copy()
            df["PCT_CHANGE_7D"]  = pct_change(df["TWEET_COUNT_7D"],  df["TWEET_COUNT_7D_PREV"])
            df["PCT_CHANGE_28D"] = pct_change(df["TWEET_COUNT_28D"], df["TWEET_COUNT_28D_PREV"])

            # round & pretty
            for c in ["PCT_OF_TWEETS_7D","PCT_OF_TWEETS_28D","PCT_CHANGE_7D","PCT_CHANGE_28D","AVG_SCORE_7D","AVG_SCORE_28D"]:
                if c in df.columns:
                    df[c] = df[c].astype(float).round(1)

            show = df[[
                "CATEGORY",
                "TWEET_COUNT_7D","PCT_OF_TWEETS_7D","PCT_CHANGE_7D",
                "TWEET_COUNT_28D","PCT_OF_TWEETS_28D","PCT_CHANGE_28D",
                # optionally:
                # "AVG_SCORE_7D","AVG_SCORE_28D"
            ]].rename(columns={
                "CATEGORY":"Category",
                "TWEET_COUNT_7D":"7d count",
                "PCT_OF_TWEETS_7D":"7d %",
                "PCT_CHANGE_7D":"7d % Δ",
                "TWEET_COUNT_28D":"28d count",
                "PCT_OF_TWEETS_28D":"28d %",
                "PCT_CHANGE_28D":"28d % Δ",
            })
            st.dataframe(show
                         , use_container_width=True, hide_index=True
                         )
            
            # show2=show.style.format({"7d %": "{:.1f}", "7d % Δ": "{:+.1f}", "28d %": "{:.1f}", "28d % Δ": "{:+.1f}"})
            # st.table(show2)




            # optional quick chart for 7d share
            try:
                st.bar_chart(show.set_index("Category")["7d % of Tweets"], use_container_width=True)

            except Exception:
                pass

# # For direct run (optional)
# if __name__ == "__main__":
#     ()
