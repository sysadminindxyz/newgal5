# tweets_widget_async.py (snippets)
from __future__ import annotations
import asyncio, base64
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import pandas as pd
import streamlit as st
from playwright.async_api import async_playwright
from db import fetch_df  # root-level import (db.py sits at project root)
import re, json

# st.cache_data.clear()
# st.cache_resource.clear()
# from pathlib import Path
# from os import getenv
# cache_dir = Path(getenv("TWEET_IMG_CACHE_DIR", "~/.cache/snacklash/tweets")).expanduser()
# removed = 0
# for p in cache_dir.glob("*.png"):
#     try:
#         if p.stat().st_size < 8000:  # tiny/blank shots
#             p.unlink(); removed += 1
#     except Exception:
#         pass
# print("Removed small PNGs:", removed)


_id_re = re.compile(r"(?:status/|status%2F|i/web/status/)(\d+)")
def _extract_id(u: str) -> Optional[str]:
    m = _id_re.search(u.strip())
    return m.group(1) if m else None

def _normalize(u: str) -> str:
    # Normalize host only; we'll rely on ID for the iframe src
    return re.sub(r"^https?://x\.com/", "https://twitter.com/", u.strip())

def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()

EMBED_THEME = "dark"   # or "light"
VIEWPORT_W  = 600
TIMEOUT_MS  = 50000

_id_re = re.compile(r"(?:status/|status%2F|i/web/status/)(\d+)")
def _extract_id(u: str) -> Optional[str]:
    m = _id_re.search(u.strip())
    return m.group(1) if m else None

async def _render_batch(urls: List[str]) -> List[Optional[bytes]]:
    """
    Render N tweets on one page with widgets.js.
    We programmatically create each tweet by ID, scroll into view,
    wait for dynamic height, then screenshot the container.
    """
    if not urls:
        return []

    # Build container IDs and extract IDs (keep order)
    cids: List[str] = []
    ids: List[Optional[str]] = []
    for i, raw in enumerate(urls):
        tid = _extract_id(raw)
        cid = f"t-{tid or f'i{i}'}"
        cids.append(cid)
        ids.append(tid)

    # Empty containers; we'll fill them via twttr.widgets.createTweet(id, el, opts)
    containers_html = "\n".join(
        f'<div id="{cid}" style="margin:0 0 16px 0;"></div>' for cid in cids
    )

    html = f"""
    <!doctype html><meta charset="utf-8"/>
    <style>
      html,body {{ margin:0; background:#fff; }}
      #wrap      {{ width:{VIEWPORT_W}px; margin:0 auto; }}
      /* no fixed heights: let widgets.js resize */
    </style>
    <div id="wrap">
      {containers_html}
    </div>
    <script>
      window.__TWEET_IDS__  = {json.dumps(ids)};
      window.__CONTAINER_IDS__ = {json.dumps(cids)};
      function boot() {{
        if (!window.twttr || !twttr.widgets || !twttr.widgets.createTweet) {{
          return setTimeout(boot, 100);
        }}
        for (var i=0;i<__TWEET_IDS__.length;i++) {{
          var id  = __TWEET_IDS__[i];
          var cid = __CONTAINER_IDS__[i];
          var el  = document.getElementById(cid);
          if (!el) continue;
          if (!id) {{ el.innerHTML = ""; continue; }}
          // Render by ID; no username needed
          twttr.widgets.createTweet(id, el, {{
            theme: "{EMBED_THEME}",
            conversation: "none",
            align: "center"
          }});
        }}
      }}
      window.addEventListener('load', boot);
    </script>
    <script async src="https://platform.twitter.com/widgets.js"></script>
    """

    out: List[Optional[bytes]] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": VIEWPORT_W + 40, "height": 3000},
            device_scale_factor=2,
            user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        )
        page = await ctx.new_page()
        await page.set_content(html, wait_until="load", timeout=TIMEOUT_MS)

        # Let widgets.js initialize
        await page.wait_for_timeout(800)

        for cid in cids:
            png: Optional[bytes] = None
            try:
                # ensure lazy loads fire
                await page.evaluate("""id => {
                    const el = document.getElementById(id);
                    if (el) el.scrollIntoView({block: 'center'});
                }""", cid)

                # wait specifically for THIS container to grow & contain an iframe
                try:
                    await page.wait_for_function(
                        """id => {
                            const c = document.getElementById(id);
                            if (!c) return false;
                            const f = c.querySelector('iframe[src*="platform.twitter.com"]');
                            const h = c.getBoundingClientRect().height;
                            return !!f && (h > 140 || (f && f.clientHeight > 140));
                        }""",
                        arg=cid,
                        timeout=16000,
                    )
                except Exception:
                    # still try to capture whatever is there
                    pass

                el = await page.query_selector(f"#{cid}")
                png = await (el.screenshot(type="png") if el else page.screenshot(type="png"))
            except Exception:
                png = None
            out.append(png)

        await ctx.close(); await browser.close()
    return out

@st.cache_data(ttl=600, show_spinner=False)
def get_recent_tweet_images_b64_and_urls(limit: int = 10) -> List[List[str]]:
    """
    Returns [[image_b64, tweet_url], ...] newest first using direct iframe embeds by ID.
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