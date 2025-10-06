# tweets_to_image.py
from __future__ import annotations
import base64
from typing import List, Tuple, Optional

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import streamlit as st

from db import fetch_df  # ← your shared Snowflake fetcher

EMBED_THEME = "dark"   # or "light"
VIEWPORT_W = 600       # tweet width in px
TIMEOUT_MS = 15000

@st.cache_resource(show_spinner=False)
def _get_browser():
    pw = sync_playwright().start()
    # Headless Chromium
    browser = pw.chromium.launch(headless=True)
    return pw, browser

def _render_tweet_png(tweet_url: str) -> bytes:
    """
    Render a single tweet URL to a PNG bytes using Twitter's widgets.js.
    """
    html = f"""
    <!doctype html>
    <meta charset="utf-8"/>
    <style>
      html,body{{margin:0;padding:0;background:#000;color:#fff}}
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
        # Wait for the embed iframe to appear and finish sizing
        page.wait_for_selector('iframe[src*="platform.twitter.com"]', timeout=TIMEOUT_MS)
        page.wait_for_timeout(1000)  # small settle time

        # Screenshot just the rendered widget (iframe’s bounding box)
        iframe_el = page.query_selector('iframe[src*="platform.twitter.com"]')
        if not iframe_el:
            raise PWTimeout("Tweet iframe not found")
        png = iframe_el.screenshot(type="png")
        return png
    finally:
        page.close()
        ctx.close()

@st.cache_data(show_spinner=False, ttl=600)
def get_recent_tweet_images_b64(limit: int = 10) -> List[str]:
    """
    Returns a list of base64 PNG strings (newest first) for recent tweets.
    """
    df: pd.DataFrame = fetch_df(f"""
        SELECT TWEET_TEXT, TWEET_URL, CREATED_AT
        FROM MART.TWEET_MEDIA
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}
    """)

    # Ensure proper sort and drop rows missing URLs
    df = df.dropna(subset=["TWEET_URL"]).sort_values("CREATED_AT", ascending=False)

    images_b64: List[str] = []
    for _, row in df.iterrows():
        url = str(row["TWEET_URL"])
        try:
            png_bytes = _render_tweet_png(url)
            images_b64.append(base64.b64encode(png_bytes).decode("ascii"))
        except Exception as e:
            # Optional: fallback – make a simple text card if embed fails
            # For brevity we skip; you can log with st.warning(f"Failed: {e}")
            continue
    return images_b64
