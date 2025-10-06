# db.py
import pandas as pd
import streamlit as st
import snowflake.connector
from cryptography.hazmat.primitives import serialization
import base64
from .config import load_config

@st.cache_resource
def get_conn():
    cfg = load_config()
    key = serialization.load_pem_private_key(
        base64.b64decode(cfg["PRIVATE_KEY_PEM_B64"]),
        password=(cfg.get("PRIVATE_KEY_PASSPHRASE") or "").encode() or None,
    ).private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return snowflake.connector.connect(
        account=cfg["SNOWFLAKE_ACCOUNT"],
        user=cfg["SNOWFLAKE_USER"],
        role=cfg["SNOWFLAKE_ROLE"],
        warehouse=cfg["SNOWFLAKE_WAREHOUSE"],
        database=cfg["SNOWFLAKE_DATABASE"],
        schema=cfg["SNOWFLAKE_SCHEMA"],
        private_key=key,
        client_session_keep_alive=True,
    )

@st.cache_data(ttl=300)
def fetch_df(sql: str, params=None) -> pd.DataFrame:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or {})
        return cur.fetch_pandas_all()   # ← no pandas/sqlalchemy warning
    finally:
        cur.close()
