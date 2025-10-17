import os, sys, pandas as pd
import streamlit as st
import csv
import json
from db import summarize_windows

# paths
# central_pipeline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'central-pipeline'))
# sys.path.append(central_pipeline_path)

#from indxyz_utils.widgetbox import main as wb
from .indxyz_utils.indxyz_utils.widgetbox_ticker import main as wb 
from .parse_rss import rss_as_tuples


# === Mock Function to Return News (no filtering yet) ===
# def get_news(source_type, time_selection):
#     return(rss_as_tuples(limit=100))

def build_html(items):
    return "<ul>" + "\n".join(items) + "</ul>"

def main():
  #NEWS

    # === Dummy Data Refresh (on every interaction) ===
    # news = get_news("", "")
    news= rss_as_tuples(limit=100)
    rss_counts = summarize_windows("RAW.RSS_ARTICLES", "PULLED_AT")
    #print(rss_counts)

    #print(rss_counts)
    # === News Widget HTML ===
    html_parts_news  = [wb(" News Media", "newspaper" 
                      ,[rss_counts["day"]["count"],rss_counts["week"]["count"],rss_counts["d28"]["count"]]
                      , [rss_counts["day"]["delta"],rss_counts["week"]["delta"],rss_counts["d28"]["delta"]])
                      ]
    html_parts_news.append("""
        </div>
        <div style="
            height: 305px;
            overflow-y: auto;
            padding: 0px 15px;
            background-color: #f9f9f9;
            font-family: Arial, sans-serif; /* ← Added font family */

        ">
    """)

    html_parts_news.append("""
 
    <ol style="margin-left: -30px; margin-bottom: 10px;" type="1">
    """)

    for title, desc, sources in news:
        html_parts_news.append(f"""
            <li style="margin-bottom: 10px;">
                <strong>{title}</strong>
                <ul style="padding-left: 16px; margin-top: 5px;">
                        <span class="desc">{desc}</span><br>
        """)
        for source_text, url in sources:
            html_parts_news.append(f'<a class="source-link" href="{url}" target="_blank">{source_text}</a>')
            #html_parts_news.append(f'{impact}')
        html_parts_news.append("""</ul></li>""")
    


    return("".join(html_parts_news))

if __name__ == "__main__":
    main()
