import streamlit as st
import streamlit.components.v1 as components
import csv
import base64
import os
import re
import sys
import json
from .indxyz_utils.indxyz_utils.widgetbox_ticker import main as wb
from .indxyz_utils.indxyz_utils.tweet_to_image_tools import get_base64_image
from .indxyz_utils.indxyz_utils.tweet_to_image_tools import extract_tweet_id


def main():
    # # Add the absolute path to central-pipeline to sys.path
    # central_pipeline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..', 'central-pipeline'))
    # sys.path.append(central_pipeline_path)
    # from indxyz_utils.widgetbox import main as wb
    # from indxyz_utils.tweet_to_image_tools import get_base64_image, extract_tweet_id



    #########SOCIAL MEDIA POST IMAGES
    # === Dummy Data Refresh (on every interaction) ===
    tweet_list=[]
    with open('data/toptweets.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            if len(row) == 3:
                tweet_list.append(row)
            else:
                raise ValueError(f"Unexpected row length: {row}")

    tweet_img64=[]
    for tweet in tweet_list[:10]:
        tweet_id=extract_tweet_id(tweet[2])
        tweet_img64.append(get_base64_image(f"images/social/tweet_{tweet_id}.png"))


    html_parts  = [wb(" Social Conversation", "twitter" 
                      , ['7','58','156'], ['-100%','+27%','-4%'])]
    html_parts.append("""
        </div>
        <div style="
            height: 250px;
            overflow-y: auto;
            padding: 10px 15px;
            background-color: #f9f9f9;
            font-family: Arial, sans-serif; /* ← Added font family */

        ">
    """)
    # Append content inside the scrollable area
    for cnt, (title, desc, link) in enumerate(tweet_list[:10]):
        base64_img = tweet_img64[cnt]
        html_parts.append(f"""
            <div style='margin-bottom: 20px;'>
            <center>
            <a href="https://{link}" target="_blank" rel="noopener noreferrer">
            <img src="data:image/png;base64,{base64_img}"
                style="max-width:100%; height:auto; display:block; cursor:pointer;">
            </a>
            </center>
            </div>

        """)

        #     <div style='margin-bottom: 20px;'>
        #         <img src="data:image/png;base64,{base64_img}" width="300">
        #         <br>
        #         <a class="source-link" href="{link}" target="_blank">link</a>
        #     </div>

    # Close the inner scrollable container and outer box
    html_parts.append("</div></div>")
    return("".join(html_parts))


if __name__ == "__main__":
    main()