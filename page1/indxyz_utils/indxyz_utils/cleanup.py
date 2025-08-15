# import pandas as pd
import re
import unicodedata
import emoji
import html
import re
import html


def clean_txt(text):
    if not isinstance(text, str):
        print("Error: Not a string")
        return text

    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)

    # Decode HTML entities
    text = html.unescape(text)
    
    # # Remove brackets
    # text = re.sub(r'\[', '', text)
    # text = re.sub(r'\]', '', text)
    
    # # Remove parentheses content
    # text = re.sub(r'\(', '', text)
    # text = re.sub(r'\)', '', text)
    
    # Remove hashtags
    text = re.sub(r'#\S+', '', text)
    
    # remove URLs
    text = re.sub(r"https\S+|http\S+|www\.\S+", "", text)

    # # Replace usernames
    # text = re.sub(r"@\S+", "", text)

    # Remove quotes
    text = text.replace("'", "").replace('"', "").replace("’", "").replace("‘", "").replace("“", '').replace("”", '')

    # Remove emojis
    text=emoji.replace_emoji(text, replace='')

    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

    # Remove commas
    text = text.replace(',', '')
    
    # Remove ellipses
    text = re.sub(r'\.\.\.|…', '.', text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    #extraneous return \n
    text = text.replace('\n', ' ').replace('\r', ' ')

    #semicolon
    text = text.replace(";", ".")

    #COLON
    text = text.replace(":", " ")

    # Remove extra punctuation, especially trailing ellipses or incomplete sequences
    text = re.sub(r'\.\.\.+', '.', text)

    # Final trim
    text = text.strip()


    return text


def dedupe_df(df, colslist, joint=False):
    if(joint):
        df.drop_duplicates(subset=colslist, inplace=True)
    else:
        for cl in colslist:
            df.drop_duplicates(subset=cl, inplace=True)


def replace_synonyms(text, synonyms, replacement):
    if not isinstance(text, str):
        print("Error: Not a string")
        return text
    pattern = r'\b(?:' + '|'.join(map(re.escape, synonyms)) + r')\b'
    return re.sub(pattern, replacement, text, flags=re.IGNORECASE)

