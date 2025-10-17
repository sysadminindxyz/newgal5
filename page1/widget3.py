# widget3.py
import streamlit as st
import streamlit.components.v1 as components
from .indxyz_utils.indxyz_utils.widgetbox_ticker import main as wb
#from .tweets_widget_async import get_recent_tweet_images_b64_and_urls  # ← NEW
from .cache_tweets import get_recent_tweet_images_b64_and_urls
from db import summarize_windows


# render items as you already do


def main():
    
    tweet_counts = summarize_windows("RAW.TWITTER_TWEETS", "CREATED_AT")
    print(tweet_counts)
    
    html_parts = []
    html_parts.append(wb(" Social Conversation", "twitter"
                      , [tweet_counts["day"]["count"],tweet_counts["week"]["count"],tweet_counts["d28"]["count"]]
                      , [tweet_counts["day"]["delta"],tweet_counts["week"]["delta"],tweet_counts["d28"]["delta"]]
                      )
    )
    html_parts.append("""
        </div>
      <div style="
          height: 285px; 
          overflow-y: auto; padding: 10px 50px;
          background-color: #f9f9f9; font-family: Arial, sans-serif; border-radius: 12px;">
    """)

    items = get_recent_tweet_images_b64_and_urls(limit=10)
    if not items:
        html_parts.append("<div style='color:#666'>No tweet images yet.</div>")
        st.write("No tweet images yet.")  # temporary
        
    for b64, tweet_url in items:
        html_parts.append(f"""
          <div style="margin-bottom: 20px; text-align:center;">
            <a href="{tweet_url}" target="_blank" rel="noopener noreferrer" >
              <img src="data:image/png;base64,{b64}"
                   alt="Tweet" style="max-width:100%; height:auto; display:block;
                   cursor:pointer; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,.08);" />
            </a>
          </div>
        """)

    #style="display:inline-block;"

    html_parts.append("</div>")
    return "".join(html_parts)
