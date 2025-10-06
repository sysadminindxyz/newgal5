# tweets_widget.py
from __future__ import annotations
import base64
from typing import List
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import streamlit as st
from .db import fetch_df

EMBED_THEME   = "dark"      # or "light"
VIEWPORT_W    = 600         # px
TIMEOUT_MS    = 15000

@st.cache_resource(show_spinner=False)
def _get_browser():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    return pw, browser

def _render_tweet_png(tweet_url: str) -> bytes:
    html = f"""
    <!doctype html>
    <meta charset="utf-8"/>
    <style>
      html,body{{margin:0;padding:0;background:#000;}}
      #wrap{{width:{VIEWPORT_W}px;margin:0 auto}}
    </style>
    <div id="wrap">
      <blockquote class="twitter-tweet" data-theme="{EMBED_THEME}">
        <a href="{tweet_url}"></a>
      </blockquote>
    </div>
    <script async src="https://platform.twitter.com/widgets.js"></script>
    """
    pw, browser = _get_browser()
    ctx = browser.new_context(viewport={"width": VIEWPORT_W + 40, "height": 1200}, device_scale_factor=2)
    page = ctx.new_page()
    try:
        page.set_content(html, wait_until="load", timeout=TIMEOUT_MS)
        page.wait_for_selector('iframe[src*="platform.twitter.com"]', timeout=TIMEOUT_MS)
        page.wait_for_timeout(1000)  # settle
        iframe_el = page.query_selector('iframe[src*="platform.twitter.com"]')
        if not iframe_el:
            raise PWTimeout("Tweet iframe not found")
        return iframe_el.screenshot(type="png")
    finally:
        page.close()
        ctx.close()

@st.cache_data(show_spinner=False, ttl=600)
def get_recent_tweet_images_b64_and_urls(limit: int = 10) -> List[List[str]]:
    """
    Returns [[image_b64, tweet_url], ...] sorted by CREATED_AT DESC.
    """
    df: pd.DataFrame = fetch_df(f"""
        SELECT TWEET_TEXT, TWEET_URL, CREATED_AT
        FROM MART.TWEET_MEDIA
        WHERE TWEET_URL IS NOT NULL
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}
    """)
    df = df.dropna(subset=["TWEET_URL"]).sort_values("CREATED_AT", ascending=False)

    out: List[List[str]] = []
    for _, row in df.iterrows():
        url = str(row["TWEET_URL"])
        try:
            png = _render_tweet_png(url)
            out.append([base64.b64encode(png).decode("ascii"), url])
        except Exception:
            # you can log with st.warning(...) if you want visibility
            continue
    return out
