# config.py
import os, json, base64
from pathlib import Path
from typing import Dict, Any

def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv, find_dotenv
        # project-local secrets/.env → then central ~/dev/secrets/.env
        if not load_dotenv(find_dotenv("secrets/.env", usecwd=True), override=False):
            central = Path.home() / "dev" / "secrets" / ".env"
            if central.exists():
                load_dotenv(central, override=False)
    except Exception:
        pass

def load_config() -> Dict[str, Any]:
    # 1) Streamlit secrets (works w/ .streamlit/secrets.toml locally)
    try:
        import streamlit as st
        if getattr(st, "secrets", None) and len(st.secrets):
            return dict(st.secrets)
    except Exception:
        pass

    # 2) AWS Secrets Manager (opt-in with USE_AWS_SECRETS=1)
    if os.getenv("USE_AWS_SECRETS", "0") == "1":
        import boto3
        name = os.getenv("SF_SECRET_NAME", "snowflake-ec2-streamlit_connect")
        region = os.getenv("AWS_REGION", "us-east-1")
        sm = boto3.client("secretsmanager", region_name=region)
        val = sm.get_secret_value(SecretId=name)
        raw = val.get("SecretString") or base64.b64decode(val["SecretBinary"])
        return json.loads(raw)

    # 3) Env / .env fallback
    _maybe_load_dotenv()
    keys = [
        "SNOWFLAKE_ACCOUNT","SNOWFLAKE_USER","SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE","SNOWFLAKE_DATABASE","SNOWFLAKE_SCHEMA",
        "PRIVATE_KEY_PEM_B64","PRIVATE_KEY_PASSPHRASE"
    ]
    cfg = {k: os.getenv(k, "") for k in keys}
    missing = [k for k,v in cfg.items() if k!="PRIVATE_KEY_PASSPHRASE" and not v]
    if missing:
        raise RuntimeError(f"Missing config values: {missing}")
    return cfg
