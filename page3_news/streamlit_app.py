    # rss_feeds = {
    #     "NYT Health": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    #     "NYT Well Blog": "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    #     "BBC Health": "http://feeds.bbci.co.uk/news/health/rss.xml",
    #     "Fox Health": "https://www.foxnews.com/about/rss/feedburner/foxnews/health",
    #     "CNN Health": "http://rss.cnn.com/rss/edition_health.rss",
    #     "Body Mysteries Blog": "https://bodymysteries.com/feed/",
    #     "Precision Nutrition Blog": "https://www.precisionnutrition.com/blog/feed", 
    #     "My Fitness Pal Blog": "https://blog.myfitnesspal.com/feed",
    #     "Wellness Mama Blog": "https://wellnessmama.com/feed",
    #     "Mobi Health News": "https://www.mobihealthnews.com/feed",
    #     "Health Partners Blog": "https://www.healthpartners.com/blog/feed/",
    #     "Sound Health Blog": "https://soundhealthandlastingwealth.com/feed/",
    #     "Suntrics Health Blog": "https://suntrics.com/category/health-blogs/feed/",
    #     "Healthsoothe Blog": "https://healthsoothe.com/feed/",
    #     "You Must Get Healthy Blog": "https://youmustgethealthy.com/feed/",
    #     "Be Healthy Now Blog": "https://www.behealthynow.co.uk/feed/",
    #     "Talk Health Blog": "https://www.talkhealthpartnership.com/blog/feed/",
    #     "JS Health Blog": "https://jessicasepel.com/feed/",
    #     "Black Health Matters Blog": "https://blackhealthmatters.com/feed/",
    #     "Best Health Guidlines Blog": "https://besthealthguidelines.com/feed/",
    #     "Brain Based Health Blog": "https://www.brainbasedhealth.org/rss/",
    # }
import streamlit as st
from datetime import datetime
import feedparser
import pandas as pd

# --- PSEUDO DATABASE FUNCTIONS ---
def load_from_db(table_name):
    """Replace this with real DB fetch logic."""
    return st.session_state.get(table_name, {})

def save_to_db(table_name, data):
    """Replace this with real DB save logic."""
    st.session_state[table_name] = data

# --- RSS FEED PARSER ---
def parse_rss_feed(url, source_name):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        try:
            published_time = datetime(*entry.published_parsed[:6])
        except:
            published_time = datetime.now()
        articles.append({
            "id": entry.link,
            "title": entry.title,
            "link": entry.link,
            "description": entry.summary,
            "published_at": published_time,
            "source": source_name
        })
    return articles

# --- STREAMLIT APP ---
def main():
    st.set_page_config(layout="wide")
    st.title("Tending News Articles")
    
    rss_feeds = {
        "NYT - Health": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "NYT - Well Blog": "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
        "BBC - Health": "http://feeds.bbci.co.uk/news/health/rss.xml",
        "Fox Health": "https://www.foxnews.com/about/rss/feedburner/foxnews/health",
        "CNN Health": "http://rss.cnn.com/rss/edition_health.rss",
    }

    # --- USER CONTROLS (Compact Layout) ---
    feed_options = ["All Sources"] + list(rss_feeds.keys())
    selected = st.selectbox("🗂️ Select Feed:", feed_options)

    col1, col2 = st.columns([2, 3])  # Adjust width ratios as needed

    with col1:
        keyword = st.text_input("🔍 Keyword", placeholder="Type to filter...")

    with col2:
       date_range = st.date_input(
           "📅 Date range",
           [datetime.today().replace(month=1, day=1), datetime.today()],
           label_visibility="visible"
       )

    # --- LOAD DB ---
    favs = load_from_db("favorites")  # {article_id: True}
    tags = load_from_db("tags")       # {article_id: ["tag1", "tag2"]}

    # --- FETCH ARTICLES ---
    sources = [(name, url) for name, url in rss_feeds.items()] if selected == "All Sources" else [(selected, rss_feeds[selected])]
    raw_articles = []
    for name, url in sources:
        raw_articles += parse_rss_feed(url, name)

    # --- DE-DUPE ---
    articles_dict = {a["id"]: a for a in raw_articles}
    articles = list(articles_dict.values())

    # --- FILTER ---
    start, end = datetime.combine(date_range[0], datetime.min.time()), datetime.combine(date_range[1], datetime.max.time())
    filtered = [
        a for a in articles
        if start <= a["published_at"] <= end and
           (keyword.lower() in a["title"].lower() or keyword.lower() in a["description"].lower())
    ] if keyword else [a for a in articles if start <= a["published_at"] <= end]

    filtered = sorted(filtered, key=lambda x: x["published_at"], reverse=True)
    st.write(f"📌 Showing {len(filtered)} articles")

    # --- DISPLAY ARTICLES ---
    for a in filtered:
        st.markdown(f"## {a['title']}")
        st.caption(f"📰 Source: {a['source']}  |  📅 {a['published_at'].strftime('%Y-%m-%d %H:%M')}")
        st.write(a["description"])
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            is_fav = favs.get(a["id"], False)
            if st.button("⭐ Favorite" if not is_fav else "❌ Unfavorite", key="fav_"+a["id"]):
                favs[a["id"]] = not is_fav
                save_to_db("favorites", favs)

        with col2:
            current_tags = tags.get(a["id"], [])
            new_tag = st.text_input("Add tag", key="tag_input_"+a["id"])
            if st.button("➕ Tag", key="tag_btn_"+a["id"]) and new_tag:
                current_tags.append(new_tag)
                tags[a["id"]] = list(set(current_tags))
                save_to_db("tags", tags)

        with col3:
            st.write("🏷️ Tags:", ", ".join(tags.get(a["id"], [])) or "None")

        st.markdown(f"[🔗 Read more]({a['link']})")
        st.markdown("---")

    # --- EXPORT CSV ---
    if filtered:
        df = pd.DataFrame(filtered)
        df["is_favorite"] = df["id"].apply(lambda i: favs.get(i, False))
        df["tags"] = df["id"].apply(lambda i: ";".join(tags.get(i, [])))
        st.download_button("📥 Export Filtered Articles", df.to_csv(index=False), file_name="filtered_articles.csv")

        df_fav = df[df["is_favorite"]]
        if not df_fav.empty:
            st.download_button("📥 Export Favorites", df_fav.to_csv(index=False), file_name="favorite_articles.csv")

if __name__ == "__main__":
    main()

