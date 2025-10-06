# debug_tweets.py
import streamlit as st
from .db import fetch_df

def show_recent_tweet_urls(limit=5):
    df = fetch_df(f"""
        SELECT TWEET_URL, CREATED_AT
        FROM MART.TWEET_MEDIA
        WHERE TWEET_URL IS NOT NULL
        ORDER BY CREATED_AT DESC
        LIMIT {int(limit)}
    """)
    st.write("Recent tweet URLs:", df[["TWEET_URL", "CREATED_AT"]])
