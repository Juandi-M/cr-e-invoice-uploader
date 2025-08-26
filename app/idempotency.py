"""
Idempotencia con Azure Table: evita reproceso por (tenant, messageId, hash).
"""
from typing import Optional
from azure.data.tables import TableServiceClient, UpdateMode
from app.config import settings
import hashlib, time

TABLE_NAME = "idempotency"

def _table():
    svc = TableServiceClient.from_connection_string(settings.storage_conn)
    try:
        svc.create_table(TABLE_NAME)
    except Exception:
        pass
    return svc.get_table_client(TABLE_NAME)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def row_key(tenant: str, message_id: str, content_hash: str) -> str:
    return f"{message_id}|{content_hash}"

def already_processed(tenant: str, message_id: str, content_hash: str) -> bool:
    tbl = _table()
    try:
        e = tbl.get_entity(tenant, row_key(tenant, message_id, content_hash))
        return e is not None
    except Exception:
        return False

def mark(tenant: str, message_id: str, content_hash: str, stage: str, note: Optional[str] = None):
    tbl = _table()
    entity = {
        "PartitionKey": tenant,
        "RowKey": row_key(tenant, message_id, content_hash),
        "messageId": message_id,
        "hash": content_hash,
        "stage": stage,
        "note": note or "",
        "ts": int(time.time()),
    }
    tbl.upsert_entity(entity=entity, mode=UpdateMode.MERGE)
