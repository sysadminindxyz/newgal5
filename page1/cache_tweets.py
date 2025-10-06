# cache_tweets.py
### THIS IS A WRAPPER FOR tweets_widget_async.PY TO ADD DISK CACHING OF TWEET IMAGES + L1 STREAMLIT CACHING
from __future__ import annotations
import os, re, base64, asyncio
from pathlib import Path
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import pandas as pd

from .db import fetch_df
# Reuse your existing helpers from tweets_widget_async.py
from .tweets_widget_async import _render_batch  # batch renderer (async)
from .tweets_widget_async import _normalize     # x.com -> twitter.com (or copy same regex here)

# -------- disk cache location --------
CACHE_DIR = Path(os.getenv("TWEET_IMG_CACHE_DIR", "~/.cache/snacklash/tweets")).expanduser()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_tid_re = re.compile(r"/status/(\d+)")

def _tweet_id(url: str) -> Optional[str]:
    m = _tid_re.search(url)
    return m.group(1) if m else None

def _read_b64(path: Path) -> Optional[str]:
    try:
        return base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception:
        return None

def _write_png_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)

def _run_async(coro):
    # Run an async coroutine from Streamlit safely
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(lambda: asyncio.run(coro)).result()

@st.cache_data(show_spinner=False)
def get_or_render_one(tweet_url: str) -> Optional[str]:
    """Return base64 PNG for one tweet, using disk cache; render if missing."""
    url = _normalize(tweet_url)
    tid = _tweet_id(url)
    if not tid:
        return None
    f = CACHE_DIR / f"{tid}.png"

    # L2 disk hit
    if f.exists():
        b64 = _read_b64(f)
        if b64:
            return b64

    # Miss → render just this one via the batch renderer
    pngs = _run_async(_render_batch([url]))
    png = pngs[0] if pngs else None
    if not png:
        return None

    _write_png_atomic(f, png)
    return base64.b64encode(png).decode("ascii")

@st.cache_data(ttl=600, show_spinner=False)
def get_recent_tweet_images_b64_and_urls(limit: int = 10) -> List[List[str]]:
    """
    Pull newest N TWEET_URLs from MART.TWEET_MEDIA and return [[b64, url], ...].
    Uses L2 disk cache (by tweet_id) + L1 Streamlit cache for the function result.
    """
    df: pd.DataFrame = fetch_df(f"""
        SELECT TWEET_URL, CREATED_AT
        FROM MART.TWEET_MEDIA
        WHERE TWEET_URL IS NOT NULL
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}
    """).dropna(subset=["TWEET_URL"])

    urls = [_normalize(str(u)) for u in df["TWEET_URL"]]

    # 1) try disk for each
    have: dict[str, str] = {}
    missing: List[str] = []
    for u in urls:
        tid = _tweet_id(u)
        if not tid:
            continue
        f = CACHE_DIR / f"{tid}.png"
        if f.exists():
            b64 = _read_b64(f)
            if b64:
                have[u] = b64
                continue
        missing.append(u)

    # 2) render misses as a single batch
    if missing:
        pngs = _run_async(_render_batch(missing))
        for u, png in zip(missing, pngs):
            if not png:
                continue
            tid = _tweet_id(u)
            if not tid:
                continue
            _write_png_atomic(CACHE_DIR / f"{tid}.png", png)
            have[u] = base64.b64encode(png).decode("ascii")

    # 3) emit in original (newest-first) order
    out: List[List[str]] = []
    for u in urls:
        b64 = have.get(u)
        if b64:
            out.append([b64, u])
    return out
