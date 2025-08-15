

def get_top_tweet_urls(df, n=5):
    top_tweets = df.nlargest(n, 'reply_count')
    tweet_urls = [
    f"https://x.com/{row['author_username']}/status/{row['id']}"
    for _, row in top_tweets.iterrows()
    ]
    return tweet_urls


