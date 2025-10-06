import requests
import pandas as pd
from playwright.sync_api import sync_playwright
import snowflake.connector
import os

def process_new_tweets():
    # 1. Connect to Snowflake and get new tweets
    conn = snowflake.connector.connect(
        user='your_user',
        password='your_password',
        account='your_account',
        warehouse='your_warehouse',
        database='your_db',
        schema='your_schema'
    )
    cursor = conn.cursor()

    cursor.execute("SELECT id, tweet_id, username FROM tweets WHERE processed = FALSE")
    new_tweets = cursor.fetchall()

    if not new_tweets:
        return

    embeds = []

    for tweet in new_tweets:
        id, tweet_id, username = tweet

        # 2. Get Twitter oEmbed HTML
        oembed_url = f"https://publish.twitter.com/oembed?url=https://twitter.com/{username}/status/{tweet_id}&theme=dark"
        resp = requests.get(oembed_url)
        html_embed = resp.json()['html']

        # 3. Save HTML to Snowflake
        cursor.execute(
            "INSERT INTO tweet_embeds (tweet_id, embed_html) VALUES (%s, %s)", 
            (tweet_id, html_embed)
        )

        # 4. Render embed as image
        image_path = f"tweet_images/{tweet_id}.png"
        capture_tweet_as_image(html_embed, image_path)

        # 5. Optional: Upload to object storage or serve locally

        # 6. Mark as processed
        cursor.execute("UPDATE tweets SET processed = TRUE WHERE id = %s", (id,))

    conn.commit()
    cursor.close()
    conn.close()


def capture_tweet_as_image(html_snippet, output_path):
    """Renders tweet HTML in a headless browser and saves it as an image."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(f"""
            <html>
            <head>
                <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
            </head>
            <body>
                {html_snippet}
            </body>
            </html>
        """, wait_until='networkidle')
        page.wait_for_timeout(3000)  # allow time for JS render
        page.screenshot(path=output_path, full_page=True)
        browser.close()
