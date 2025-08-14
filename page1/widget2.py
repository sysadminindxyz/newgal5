import os, sys, pandas as pd
import streamlit as st
import csv
import json
# paths
# central_pipeline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'central-pipeline'))
# sys.path.append(central_pipeline_path)

#from indxyz_utils.widgetbox import main as wb
from indxyz_utils.widgetbox_ticker import main as wb 


# === Mock Function to Return News (no filtering yet) ===
def get_news(source_type, time_selection):
    return [   
        (
            "The snacking recession: Why Americans are buying fewer treats",
            "Americans are snacking less — and that's a problem for the packaged food industry. Why it matters: After years of inflation, consumers are recoiling, fed up with food price increases and suddenly immersed in economic uncertainty...",
            [
                ("Axios", "https://www.axios.com/2025/03/19/general-mills-snacks-sales", "Impact factor = 27, Engagement=18"),
            ]
        ),
        (
            "Why GLP-1s could become the 'everything drug'",
            "The biggest buzz around GLP-1 drugs these days has nothing to do with weight loss. And that might lead to some problems for patients and insurers...",
            [
                ("Axios", "https://www.businessoffashion.com/articles/workplace-talent/plus-size-models-fashion-industry-slowdown-90s-thinness-ozempic",
                 "Impact factor=27, Engagement=11"),
            ]
        ),
    ]

def build_html(items):
    return "<ul>" + "\n".join(items) + "</ul>"

def main():
  #NEWS
    # === Dummy Data Refresh (on every interaction) ===
    news = get_news("", "")

    # === News Widget HTML ===
    html_parts_news  = [wb(" News Media", "newspaper" 
                      ,['3','12','42'], ['+300%','+20%','-25%'])]
    html_parts_news.append("""
        </div>
        <div style="
            height: 250px;
            overflow-y: auto;
            padding: 10px 15px;
            background-color: #f9f9f9;
            font-family: Arial, sans-serif; /* ← Added font family */

        ">
    """)


    for title, desc, sources in news:
        html_parts_news.append(f"""
            <li style="margin-bottom: 10px;">
                <strong>{title}</strong>
                <ul style="padding-left: 16px; margin-top: 5px;">
                        <span class="desc">{desc}</span><br>
        """)
        for source_text, url, impact in sources:
            html_parts_news.append(f'<a class="source-link" href="{url}" target="_blank">{source_text}</a>')
            html_parts_news.append(f'{impact}')
        html_parts_news.append("""</ul></li>""")
    

    return("".join(html_parts_news))

if __name__ == "__main__":
    main()
