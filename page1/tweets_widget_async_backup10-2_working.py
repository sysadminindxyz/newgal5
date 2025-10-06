# tweets_widget_async.py  (replace existing)
from __future__ import annotations
import asyncio, base64, re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import pandas as pd
import streamlit as st
from playwright.async_api import async_playwright
from .db import fetch_df

EMBED_THEME = "dark"
VIEWPORT_W  = 600
TIMEOUT_MS  = 30000

def _normalize(u: str) -> str:
    # x.com → twitter.com helps embeds
    return re.sub(r"^https?://x\.com/", "https://twitter.com/", u.strip())

def _run_async(coro):
    # Run safely whether Streamlit already has an event loop or not
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()

async def _render_batch(urls: List[str]) -> List[Optional[bytes]]:
    """
    Render N tweets on ONE page (faster, more reliable), return list of PNG bytes
    aligned to the input order.
    """
    if not urls:
        return []
    # Build one HTML with N blockquotes
    blocks = "\n".join(
        f'<blockquote class="twitter-tweet" data-theme="{EMBED_THEME}"><a href="{u}"></a></blockquote>'
        for u in urls
    )
    html = f"""
    <!doctype html><meta charset="utf-8"/>
    <style>
      html,body{{margin:0;background:#000}}
      #wrap{{width:{VIEWPORT_W}px;margin:0 auto}}
      blockquote{{margin: 0 0 16px 0;}}
    </style>
    <div id="wrap">
      {blocks}
    </div>
    <script async src="https://platform.twitter.com/widgets.js"></script>
    """

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        # Make the viewport tall enough to lay out multiple embeds
        ctx = await browser.new_context(
            viewport={"width": VIEWPORT_W + 40, "height": 2000},
            device_scale_factor=2,
            user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        )
        page = await ctx.new_page()
        await page.set_content(html, wait_until="load", timeout=TIMEOUT_MS)

        # Wait until we have as many iframes as tweets (or timeout)
        await page.wait_for_function(
            f"() => document.querySelectorAll('iframe[src*=\"platform.twitter.com\"]').length >= {len(urls)}",
            timeout=TIMEOUT_MS,
        )
        # Give layout a moment to settle heights
        await page.wait_for_timeout(800)

        # Grab all iframes in DOM order (widgets.js renders in input order)
        frames = await page.query_selector_all('iframe[src*="platform.twitter.com"]')

        # If fewer iframes than urls (some failed), pad with None
        pngs: List[Optional[bytes]] = []
        for i in range(len(urls)):
            if i < len(frames):
                try:
                    pngs.append(await frames[i].screenshot(type="png"))
                except Exception:
                    pngs.append(None)
            else:
                pngs.append(None)

        await ctx.close()
        await browser.close()
        return pngs

@st.cache_data(ttl=600, show_spinner=False)
def get_recent_tweet_images_b64_and_urls(limit: int = 10) -> List[List[str]]:
    """
    Returns [[image_b64, tweet_url], ...] newest first.
    Uses batch rendering so you get all N images, not just the first.
    """
    df: pd.DataFrame = fetch_df(f"""
        SELECT TWEET_URL, CREATED_AT
        FROM MART.TWEET_MEDIA
        WHERE TWEET_URL IS NOT NULL
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}
    """).dropna(subset=["TWEET_URL"])

    urls = [_normalize(str(u)) for u in df["TWEET_URL"]]
    pngs = _run_async(_render_batch(urls))

    items: List[List[str]] = []
    for png, url in zip(pngs, urls):
        if png:
            items.append([base64.b64encode(png).decode("ascii"), url])
    return items
