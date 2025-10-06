# tweets_widget_async_debug.py
from __future__ import annotations
import asyncio, base64, re
from typing import List, Tuple, Optional

import pandas as pd
import streamlit as st
from playwright.async_api import async_playwright, TimeoutError
from .db import fetch_df

EMBED_THEME = "dark"
VIEWPORT_W  = 600
TIMEOUT_MS  = 30000

def _normalize_tweet_url(u: str) -> str:
    # Normalize x.com → twitter.com (reduces embed flakiness)
    return re.sub(r"^https?://x\.com/", "https://twitter.com/", u.strip())

def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()

async def _render_one_tweet(url: str) -> Tuple[Optional[bytes], str]:
    logs: List[str] = []
    html = f"""
    <!doctype html><meta charset="utf-8"/>
    <style>html,body{{margin:0}} #wrap{{width:{VIEWPORT_W}px;margin:0 auto;background:#000}}</style>
    <div id="wrap"><blockquote class="twitter-tweet" data-theme="{EMBED_THEME}">
      <a href="{url}"></a></blockquote></div>
    <script async src="https://platform.twitter.com/widgets.js"></script>
    """
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx = await browser.new_context(
                viewport={"width": VIEWPORT_W + 40, "height": 1400},
                device_scale_factor=2,
                user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            )
            page = await ctx.new_page()

            # Capture console + network for debugging
            page.on("console", lambda m: logs.append(f"CONSOLE {m.type}: {m.text}"))
            page.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e.message}"))
            page.on("response", lambda r: (
                logs.append(f"HTTP {r.status} {r.url}")
                if ("platform.twitter.com" in r.url or "cdn.syndication.twimg.com" in r.url) else None
            ))

            await page.set_content(html, wait_until="load", timeout=TIMEOUT_MS)
            await page.wait_for_selector('iframe[src*="platform.twitter.com"]', timeout=TIMEOUT_MS)
            await page.wait_for_function(
                """() => { const f = document.querySelector('iframe[src*="platform.twitter.com"]');
                           return f && f.clientHeight > 200; }""",
                timeout=TIMEOUT_MS,
            )
            wrap = await page.query_selector("#wrap")
            png = await (wrap.screenshot(type="png") if wrap else page.screenshot(type="png"))
            await ctx.close(); await browser.close()
            return png, "\n".join(logs)
    except Exception as e:
        logs.append(f"EXC: {type(e).__name__}: {e}")
        return None, "\n".join(logs)

@st.cache_data(ttl=600, show_spinner=False)
def get_images_with_urls_debug(limit: int = 10) -> Tuple[List[List[str]], List[str]]:
    df: pd.DataFrame = fetch_df(f"""
        SELECT TWEET_URL, CREATED_AT
        FROM MART.TWEET_MEDIA
        WHERE TWEET_URL IS NOT NULL
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}
    """).dropna(subset=["TWEET_URL"])

    urls = [_normalize_tweet_url(str(u)) for u in df["TWEET_URL"]]
    items: List[List[str]] = []
    dbg: List[str] = []
    for u in urls:
        png, log = _run_async(_render_one_tweet(u))
        dbg.append(f"{u}\n{log}\n---")
        if png:
            items.append([base64.b64encode(png).decode("ascii"), u])
    return items, dbg
