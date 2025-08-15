import pandas as pd
import numpy as np
import requests
import tweepy
import os
from dotenv import load_dotenv


def expand_variations(word_list):
    expanded = []
    for word in word_list:
        base = word.strip()
        if " " in base:
            base_quoted = f'"{base}"'
            possessive = f'"{base}\'s"'
            plural = f'"{base}s"'
        else:
            base_quoted = base
            possessive = f'"{base}\'s"'
            plural = f"{base}s"
        expanded.extend([base_quoted, possessive, plural])
    return expanded


def addquotes(word_list):
    expanded = []
    for word in word_list:
        base = word.strip()
        if " " in base:
            base_quoted = f'"{base}"'
        else:
            base_quoted = base
        expanded.extend([base_quoted])
    return expanded




def query_twitter(bearer_token, qry, start_time=None, end_time=None, max_results_per_call=100, total_limit=1000 ):
    """
    Pull tweets using Twitter API v2, with optional start/end time and pagination.

    Args:
        bearer_token (str): Twitter API bearer token.
        qry (str): Twitter query string.
        start_time (str): ISO start time (optional).
        end_time (str): ISO end time (optional).
        max_results_per_call (int): Tweets per request (max 100).
        total_limit (int): Total tweets to collect (approximate).

    Returns:
        pd.DataFrame: DataFrame with tweet data.
    """
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

    search_params = {
        "query": qry,
        "max_results": max_results_per_call,
        "tweet_fields": [
            "created_at",
            "author_id",
            "public_metrics",
            "lang",
            "source",
            "entities",
            "possibly_sensitive",
            "conversation_id",
            "reply_settings",
            "context_annotations",
            "referenced_tweets"
        ],
        "expansions": ["author_id"],
        "user_fields": ["username", "name", "profile_image_url", "public_metrics", "verified"],
    }

    if start_time is not None:
        search_params["start_time"] = start_time
    if end_time is not None:
        search_params["end_time"] = end_time

    tweet_data = []
    author_data = {}
    next_token = None
    total_fetched = 0

    while True:
        if next_token:
            search_params["next_token"] = next_token
        else:
            search_params.pop("next_token", None)

        response = client.search_recent_tweets(**search_params)

        # Collect author info
        if "users" in response.includes:
            for user in response.includes["users"]:
                author_data[user.id] = {
                    "author_id": user.id,
                    "author_username": user.username,
                    "author_name": user.name,
                    "author_verified": user.verified,
                    "author_followers": user.public_metrics["followers_count"] if user.public_metrics else None,
                    "author_profile_image": user.profile_image_url
                }

        if response.data:
            for tweet in response.data:
                metrics = tweet.public_metrics if tweet.public_metrics else {}
                entities = tweet.entities if tweet.entities else {}
                context_annotations = tweet.context_annotations if tweet.context_annotations else []
                referenced_tweets = tweet.referenced_tweets if tweet.referenced_tweets else []

                hashtags = [tag["tag"] for tag in entities.get("hashtags", [])]
                mentions = [mention["username"] for mention in entities.get("mentions", [])]
                urls = [url["expanded_url"] for url in entities.get("urls", [])]

                context_entities = [
                    context["entity"]["name"]
                    for context in context_annotations
                    if "entity" in context and "name" in context["entity"]
                ]

                author_info = author_data.get(tweet.author_id, {})
                if isinstance(author_info, dict):
                    tweet_dict = {
                        # all the other key-value pairs
                                                "id": tweet.id,
                        "author_id": tweet.author_id,
                        "created_at": tweet.created_at,
                        "text": tweet.text,
                        "lang": tweet.lang,
                        "source": tweet.source,
                        "retweet_count": metrics.get("retweet_count", 0),
                        "reply_count": metrics.get("reply_count", 0),
                        "like_count": metrics.get("like_count", 0),
                        "quote_count": metrics.get("quote_count", 0),
                        "hashtags": hashtags,
                        "mentions": mentions,
                        "urls": urls,
                        "possibly_sensitive": tweet.possibly_sensitive,
                        "conversation_id": tweet.conversation_id,
                        "reply_settings": tweet.reply_settings,
                        "context_entities": context_entities,
                        "referenced_tweets": referenced_tweets,
                        **author_info
                    }
                else:
                    tweet_dict = {
                        "id": tweet.id,
                        "author_id": tweet.author_id,
                        "created_at": tweet.created_at,
                        "text": tweet.text,
                        "lang": tweet.lang,
                        "source": tweet.source,
                        "retweet_count": metrics.get("retweet_count", 0),
                        "reply_count": metrics.get("reply_count", 0),
                        "like_count": metrics.get("like_count", 0),
                        "quote_count": metrics.get("quote_count", 0),
                        "hashtags": hashtags,
                        "mentions": mentions,
                        "urls": urls,
                        "possibly_sensitive": tweet.possibly_sensitive,
                        "conversation_id": tweet.conversation_id,
                        "reply_settings": tweet.reply_settings,
                        "context_entities": context_entities,
                        "referenced_tweets": referenced_tweets,
                        "author_info": author_info  # just include it as-is if not a dict
                    }

                tweet_data.append(tweet_dict)

                total_fetched += 1

                # Stop if reached total limit
                if total_fetched >= total_limit:
                    break

        # Check if there is a next_token
        meta = response.meta
        next_token = meta.get("next_token") if meta else None

        if not next_token or total_fetched >= total_limit:
            break

    # Convert to DataFrame
    df = pd.DataFrame(tweet_data)
    # df['total_reply']=df['reply_count']+df['quote_count']
    #print(df.columns)
    #df['total_reply']=df['reply_count']+df['quote_count']

    return df


def get_twitter_replies(bearer_token, df, start_time=None, end_time=None, max_results_per_call=100, total_limit=1000 ):

    conversations=df.loc[(df.reply_count+df.quote_count)>0, 'conversation_id'].unique()

    convo_df_list=list()
    for c in conversations:
        print(f"Conversation ID: {c}")
        qry = f"conversation_id:{c} lang:en -is:retweet "
        convo_df_list.append(
            query_twitter(
                bearer_token=bearer_token,
                qry=qry,
                start_time=start_time,
                end_time=end_time,
                max_results_per_call=max_results_per_call,
                total_limit=total_limit
            )
        )

    convo_df=pd.concat(convo_df_list)
    return convo_df


def query_twitter_w_replies(bearer_token, qry, start_time=None, end_time=None, max_results_per_call=100, total_limit=1000, reply_total_limit=1000 ):
    df=query_twitter(bearer_token, qry, start_time, end_time, max_results_per_call, total_limit)
    df_replies=get_twitter_replies(bearer_token, df, start_time, end_time, max_results_per_call, reply_total_limit )
    df_all=pd.concat([df, df_replies]).drop_duplicates(subset=['id']).reset_index(drop=True)
    return df_all



def get_twitter_users(user_ids, bearer_token):
    import tweepy
    import pandas as pd

    client = tweepy.Client(bearer_token=bearer_token)

    response = client.get_users(
        ids=user_ids,
        user_fields=[
            "created_at", "description", "location", "profile_image_url",
            "protected", "public_metrics", "url", "verified"
        ]
    )

    # Build author dictionary
    # author_data = {}
    author_list = []

    for user in response.data:
        user_dict = {
            "author_id": user.id,
            "author_username": user.username,
            "author_name": user.name,
            "author_description": user.description,
            "author_location": user.location,
            "author_profile_image": user.profile_image_url,
            "author_protected": user.protected,
            "author_verified": user.verified,
            "author_created_at": user.created_at,
            "author_url": user.url,
            "author_followers_count": user.public_metrics["followers_count"] if user.public_metrics else None,
            "author_following_count": user.public_metrics["following_count"] if user.public_metrics else None,
            "author_tweet_count": user.public_metrics["tweet_count"] if user.public_metrics else None,
            "author_listed_count": user.public_metrics["listed_count"] if user.public_metrics else None,
        }

        # # Add to dict (if you want quick lookup later)
        # author_data[user.id] = user_dict

        # Also add to list (if you want a DataFrame)
        author_list.append(user_dict)

    # Convert list to DataFrame
    df = pd.DataFrame(author_list)

    return df




# def get_twitter_users(user_ids, bearer_token, df, start_time=None, end_time=None, max_results_per_call=100, total_limit=1000 ):

#     client = tweepy.Client(bearer_token=bearer_token)

#     response = client.get_users(
#         ids=user_ids,
#         user_fields=[
#             "created_at", "description", "location", "profile_image_url",
#             "protected", "public_metrics", "url", "verified"
#         ]
#     )
#     df = pd.DataFrame(response.data)
#     return df
