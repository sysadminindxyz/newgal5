# streamlit_app.py
import base64
import pandas as pd
import snowflake.connector
import streamlit as st
from config import load_config

st.set_page_config(page_title="Snowflake ↔ Streamlit", layout="wide")

@st.cache_resource(show_spinner=False)
def get_conn():
    cfg = load_config()
    private_key = base64.b64decode(cfg["PRIVATE_KEY_PEM_B64"])
    kwargs = dict(
        account   = cfg["SNOWFLAKE_ACCOUNT"],
        user      = cfg["SNOWFLAKE_USER"],
        role      = cfg["SNOWFLAKE_ROLE"],
        warehouse = cfg["SNOWFLAKE_WAREHOUSE"],
        database  = cfg["SNOWFLAKE_DATABASE"],
        schema    = cfg["SNOWFLAKE_SCHEMA"],
        private_key = private_key,
        client_session_keep_alive=True,
    )
    if cfg.get("PRIVATE_KEY_PASSPHRASE"):
        kwargs["private_key_password"] = cfg["PRIVATE_KEY_PASSPHRASE"]
    return snowflake.connector.connect(**kwargs)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_df(sql: str):
    with get_conn() as conn:
        return pd.read_sql(sql, conn)

st.title("Snowflake ↔ Streamlit (dev & prod parity)")
n = st.slider("Rows", 5, 100, 25, 5)
sql = f"""
SELECT *
FROM SNACKLASH2.RAW.RSS_ARTICLES
ORDER BY PULLED_AT DESC
LIMIT {int(n)}
"""
st.dataframe(fetch_df(sql), use_container_width=True)
