# page3_news/streamlit_app.py
import re
import io
import datetime as dt
import pandas as pd
import streamlit as st

from db import fetch_df  # uses your get_conn() under the hood

DEFAULT_DB = st.secrets.get("client_db", "SNACKLASH2")
DEFAULT_SCHEMA = "RAW"
TABLE_NAME = "RSS_ARTICLES"
FQT = f"{DEFAULT_DB}.{DEFAULT_SCHEMA}.{TABLE_NAME}"

PAGE_SIZE_DEFAULT = 10
MAX_PAGE_SIZE = 100

# ----- helpers -----
def highlight_terms(text: str, terms: list[str]) -> str:
    if not text or not terms:
        return text or ""
    pattern = r"(" + "|".join(re.escape(t) for t in terms if t.strip()) + r")"
    try:
        return re.sub(pattern, r"**\1**", text, flags=re.IGNORECASE)
    except re.error:
        return text

@st.cache_data(ttl=120, show_spinner=False)
def distinct_sources(start_dt, end_dt) -> list[str]:
    where = ""
    params = {}
    if start_dt and end_dt:
        where = """
          WHERE PULLED_AT >= TO_TIMESTAMP_TZ(%(dstart)s)
            AND PULLED_AT <  TO_TIMESTAMP_TZ(%(dend)s)
        """
        params = {
            "dstart": f"{start_dt} 00:00:00 +00:00",
            "dend":   f"{end_dt} 23:59:59 +00:00",
        }

    sql = f"""
        SELECT DISTINCT COALESCE(SOURCE_NAME, SOURCE_FEED_TITLE, SOURCE_FEED_URL) AS SRC
        FROM {FQT}
        {where}
        ORDER BY SRC
    """
    df = fetch_df(sql, params)
    return [s for s in df["SRC"].dropna().astype(str).tolist() if s]


def build_where_and_params(q, start_dt, end_dt, sources, use_published_parse=False):
    """
    Build WHERE clause (as a string) and params (dict).
    """
    params: dict = {}
    clauses: list[str] = []

    # ---- Date range (only if provided) ----
    if start_dt and end_dt:
        params["dstart"] = f"{start_dt} 00:00:00 +00:00"
        params["dend"]   = f"{end_dt} 23:59:59 +00:00"
        if use_published_parse:
            clauses.append(
                """
                TRY_TO_TIMESTAMP_TZ(PUBLISHED_AT_RAW) IS NOT NULL
                AND TRY_TO_TIMESTAMP_TZ(PUBLISHED_AT_RAW) >= TO_TIMESTAMP_TZ(:dstart)
                AND TRY_TO_TIMESTAMP_TZ(PUBLISHED_AT_RAW) <= TO_TIMESTAMP_TZ(:dend)
                """
            )
        else:
            clauses.append(
                """
                PULLED_AT >= TO_TIMESTAMP_TZ(:dstart)
                AND PULLED_AT <= TO_TIMESTAMP_TZ(:dend)
                """
            )

    # ---- Source filter ----
    if sources:
        src_placeholders = []
        for i, s in enumerate(sources):
            k = f"src{i}"
            params[k] = s.lower()
            src_placeholders.append(f":{k}")
        clauses.append(
            f"""
            LOWER(COALESCE(SOURCE_NAME, SOURCE_FEED_TITLE, SOURCE_FEED_URL))
            IN ({", ".join(src_placeholders)})
            """
        )

    # ---- Keyword search ----
    if q and q.strip():
        terms = [t.strip() for t in q.split() if t.strip()]
        if terms:
            for i, t in enumerate(terms):
                k = f"kw{i}"
                params[k] = f"%{t}%"
                clauses.append(
                    f"("
                    f"TITLE ILIKE :{k} OR "
                    f"SUMMARY ILIKE :{k} OR "
                    f"CONTENT_TEXT ILIKE :{k} OR "
                    f"CONTENT_HTML ILIKE :{k}"
                    f")"
                )

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where_sql, params


def build_order_by(choice: str, use_published_parse=False) -> str:
    if choice == "Most recent":
        if use_published_parse:
            return "ORDER BY TRY_TO_TIMESTAMP_TZ(PUBLISHED_AT_RAW) DESC NULLS LAST"
        return "ORDER BY PULLED_AT DESC NULLS LAST"
    if choice == "Oldest":
        if use_published_parse:
            return "ORDER BY TRY_TO_TIMESTAMP_TZ(PUBLISHED_AT_RAW) ASC NULLS LAST"
        return "ORDER BY PULLED_AT ASC NULLS LAST"
    if choice == "Title A→Z":
        return "ORDER BY TITLE ASC NULLS LAST"
    return ""

# ----- UI -----
def main():
    st.title("Trending News Articles")
    st.caption(f"Querying {FQT}")

    with st.sidebar:
        st.header("Filters")

        # OFF by default — no date filter unless you tick the box
        use_date = st.checkbox("Filter by date range", value=False)

        start_dt = end_dt = None
        if use_date:
            import datetime as dt
            today = dt.date.today()
            default_start = today - dt.timedelta(days=30)  # just a UI default when enabled
            start_dt, end_dt = st.date_input("Date range", (default_start, today), format="YYYY-MM-DD")
            if isinstance(start_dt, tuple):  # older Streamlit compatibility
                start_dt, end_dt = start_dt

        query = st.text_input("Keywords", placeholder="e.g., semaglutide supply, pricing, marketing")
        # source list (no date filter unless chosen)
        picks = st.multiselect("Sources", options=distinct_sources(start_dt, end_dt), default=[])

        sort_by = st.selectbox("Sort by", ["Most recent", "Oldest", "Title A→Z"])
        page_size = st.number_input("Results per page", 5, MAX_PAGE_SIZE, PAGE_SIZE_DEFAULT, step=5)

        use_pub = st.checkbox(
            "Use published date (parse PUBLISHED_AT_RAW)",
            value=True,
            help="Sorts/filters by TRY_TO_TIMESTAMP_TZ(PUBLISHED_AT_RAW). Uncheck to use PULLED_AT."
        )

    #filter state
    filter_state = {
        "start": str(start_dt),
        "end": str(end_dt),
        "query": query or "",
        "sources": tuple(picks),
        "sort": sort_by,
        "use_pub": use_pub,          
        "page_size": int(page_size),
    }

    # Reset offset to 0 if filters changed
    if st.session_state.get("news_prev_filter_state") != filter_state:
        st.session_state.news_offset = 0
    st.session_state.news_prev_filter_state = filter_state

    # Pagination state
    if "news_offset" not in st.session_state:
        st.session_state.news_offset = 0

    # Build SQL
    where_sql, params = build_where_and_params(
        query, start_dt, end_dt, picks, use_published_parse=use_pub
    )
    order_sql = build_order_by(sort_by, use_published_parse=use_pub)

    # Count
    count_sql = f"SELECT COUNT(*) AS N FROM {FQT} {where_sql}"
    total = int(fetch_df(count_sql, params).iloc[0, 0])

    # Page slice
    offset = int(st.session_state.news_offset)
    limit = int(page_size)

    # Clamp offset to the last full page
    if total == 0:
        offset = 0
    else:
        max_offset = ((total - 1) // limit) * limit
        if offset > max_offset:
            offset = max_offset
            st.session_state.news_offset = offset

    can_prev = offset > 0
    can_next = (offset + limit) < total

    # TOP prev/next buttons 
    col_prev, col_next, _ = st.columns([1, 1, 6])
    with col_prev:
        if st.button("⟵ Prev", key="news_prev_top", use_container_width=True, disabled=not can_prev):
            st.session_state.news_offset = max(0, offset - limit)
            st.rerun()
    with col_next:
        if st.button("Next ⟶", key="news_next_top", use_container_width=True, disabled=not can_next):
            st.session_state.news_offset = offset + limit
            st.rerun()


    # Select list (exact columns from your schema)
    select_cols = [
        "PULLED_AT", "PUBLISHED_AT_RAW", "UPDATED_AT_RAW",
        "SOURCE_NAME", "SOURCE_FEED_TITLE", "SOURCE_FEED_URL",
        "TITLE", "SUMMARY", "CONTENT_TEXT", "CONTENT_HTML",
        "AUTHOR_NAME", "AUTHOR_EMAIL", "AUTHOR_URI",
        "URL", "IMAGE_URL", "CATEGORIES", "MATCHING_RULE_IDS", "MATCHING_TERMS",
        "GUID", "GUID_IS_PERMALINK", "ENCLOSURE_URL", "ENCLOSURE_TYPE", "ENCLOSURE_LENGTH"
    ]
    select_list = ", ".join(select_cols)

    page_sql = f"""
        SELECT {select_list}
        FROM {FQT}
        {where_sql}
        {order_sql}
        LIMIT {limit}
        OFFSET {offset}
    """
    df_page = fetch_df(page_sql, params)

    # Summary
    showing_lo = offset + 1 if total > 0 else 0
    showing_hi = min(offset + limit, total)
    st.markdown(f"**Showing {showing_lo}–{showing_hi} of {total}**")

    if df_page.empty:
        st.info("No results found. Try widening the date range or changing keywords.")
        return

    # Export current page
    export_cols = [c for c in [
        "PULLED_AT","PUBLISHED_AT_RAW","UPDATED_AT_RAW",
        "SOURCE_NAME","SOURCE_FEED_TITLE","SOURCE_FEED_URL",
        "TITLE","SUMMARY","CONTENT_TEXT","URL","AUTHOR_NAME","CATEGORIES"
    ] if c in df_page.columns]
    csv_buf = io.StringIO()
    df_page[export_cols].to_csv(csv_buf, index=False)
    st.download_button("Download CSV of current page",
                       data=csv_buf.getvalue().encode("utf-8"),
                       file_name="news_results.csv",
                       mime="text/csv")

    # Render cards
    terms = [t for t in (query.split() if query else []) if t.strip()]
    for _, r in df_page.iterrows():
        with st.container(border=True):
            title = str(r.get("TITLE") or "(No title)")
            url = r.get("URL")
            source = r.get("SOURCE_NAME") or r.get("SOURCE_FEED_TITLE") or r.get("SOURCE_FEED_URL") or "Unknown source"

            # Date priority for display
            disp_date = r.get("PUBLISHED_AT_RAW") or r.get("UPDATED_AT_RAW")
            if not disp_date:
                disp_date = r.get("PULLED_AT")

            title_disp = highlight_terms(title, terms)
            if isinstance(url, str) and url.strip():
                st.markdown(f"### [{title_disp}]({url})")
            else:
                st.markdown(f"### {title_disp}")

            st.caption(f"{source} • {disp_date}")

            summary = (r.get("SUMMARY") or "")
            body = (r.get("CONTENT_TEXT") or "")  # keep HTML out of the snippet by default
            snippet = summary if len(str(summary).strip()) >= 40 else str(body)[:240]
            snippet = highlight_terms(snippet, terms)
            if snippet:
                st.markdown(snippet)

            extras = []
            if r.get("AUTHOR_NAME"):
                extras.append(f"Author: {r.get('AUTHOR_NAME')}")
            if isinstance(url, str) and url.strip():
                extras.append(f"[Open original]({url})")
            if r.get("CATEGORIES"):
                extras.append(f"Categories: {r.get('CATEGORIES')}")
            if extras:
                st.caption(" • ".join(extras))

    # BOTTOM prev/next buttons
    bprev, bnext = st.columns([1, 1])
    with bprev:
        st.button("⟵ Prev", key="news_prev_bottom", use_container_width=True, disabled=not can_prev,
                on_click=lambda: setattr(st.session_state, "news_offset", max(0, offset - limit)))
    with bnext:
        st.button("Next ⟶", key="news_next_bottom", use_container_width=True, disabled=not can_next,
                on_click=lambda: setattr(st.session_state, "news_offset", offset + limit))


def render():
    main()

if __name__ == "__main__":
    main()
