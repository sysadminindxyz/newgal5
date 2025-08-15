import requests
import os
import csv
import re
import time
import base64
from playwright.sync_api import sync_playwright


def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- Extract tweet ID from URL ---
def extract_tweet_id(url: str) -> str:
    match = re.search(r"status/(\d+)", url)
    if match:
        return match.group(1)
    raise ValueError(f"Invalid tweet URL: {url}")

# --- Fetch tweet embed HTML with dark mode ---
def fetch_oembed_html(tweet_url: str) -> str:
    if not tweet_url.startswith("http"):
        tweet_url = f"https://{tweet_url}"
    
    # Request without script, we'll inject it manually
    api_url = f"https://publish.twitter.com/oembed?url={tweet_url}&omit_script=true"
    response = requests.get(api_url)
    response.raise_for_status()
    html = response.json()['html']

    # Add dark mode support
    html = html.replace(
        '<blockquote class="twitter-tweet"',
        '<blockquote class="twitter-tweet" data-theme="dark"'
    )

    return html

# --- Screenshot embedded tweet iframe only ---
def save_html_as_image(html: str, output_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        full_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        </head>
        <body>{html}</body>
        </html>
        """

        page.set_content(full_html, wait_until="networkidle")
        page.wait_for_selector("iframe", timeout=10000)

        # Wait a bit more to let avatar + icons load
        time.sleep(3)

        iframe = page.query_selector("iframe")
        if iframe:
            iframe.screenshot(path=output_path)
        else:
            raise RuntimeError("Could not find iframe to screenshot.")

        browser.close()

# --- Main logic for tweet list ---
def process_tweet_list(tweet_list, output_dir="images"):
    os.makedirs(output_dir, exist_ok=True)

    for tweet in tweet_list:
        tweet_text = tweet[0]
        engagement_text = tweet[1]
        tweet_url = tweet[2]

        if len(tweet) >= 4 and tweet[3]:
            continue  # Already processed

        try:
            tweet_id = extract_tweet_id(tweet_url)
            html = fetch_oembed_html(tweet_url)
            image_name = f"tweet_{tweet_id}.png"
            image_path = os.path.join(output_dir, image_name)
            save_html_as_image(html, image_path)
            tweet.append(image_name)
        except Exception as e:
            print(f"Error processing tweet: {tweet_url} -> {e}")
            tweet.append(None)

