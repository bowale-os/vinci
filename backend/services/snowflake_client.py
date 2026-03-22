"""Snowflake connection helper using RSA key-pair authentication."""
import os
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_pem_private_key,
)
import snowflake.connector

from config import settings


def _load_private_key() -> bytes:
    key_path = Path(settings.snowflake_private_key_path)
    pem_data = key_path.read_bytes()
    private_key = load_pem_private_key(pem_data, password=None, backend=default_backend())
    return private_key.private_bytes(
        encoding=Encoding.DER,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """Return a new Snowflake connection using key-pair auth."""
    return snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        private_key=_load_private_key(),
        database=settings.snowflake_database,
        schema=settings.snowflake_schema,
        warehouse=settings.snowflake_warehouse,
    )


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SQL query and return rows as list of dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor(snowflake.connector.DictCursor)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()
