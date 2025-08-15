import pandas as pd
from urllib.parse import urlparse
import asyncio



async def fetch_article_info(link, browser):
    page = await browser.new_page()
    try:
        await page.goto(link, timeout=30000)
        headline = await page.locator("h1").inner_text()  # Adjust selector per site
        paragraph = await page.locator("p").nth(0).inner_text()  # First paragraph
        domain = urlparse(link).netloc
        source_name = domain.replace("www.", "").split(".")[0].capitalize()
        return {
            "headline": headline.strip(),
            "paragraph": paragraph.strip(),
            "source": source_name,
            "link": link
        }
    except Exception as e:
        print(f"Error fetching {link}: {e}")
        return None
    finally:
        await page.close()


