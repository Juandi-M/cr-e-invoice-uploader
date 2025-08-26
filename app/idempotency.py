import hashlib, time
from typing import Optional
from azure.data.tables import TableServiceClient, UpdateMode
from app.config import settings

TABLE = "idempotency"

def _table():
    svc = TableServiceClient.from_connection_string(settings.storage_conn)
    try:
        svc.create_table(TABLE)
    except Exception:
        pass
    return svc.get_table_client(TABLE)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _rk(message_id: str, content_hash: str) -> str:
    return f"{message_id}|{content_hash}"

def already_processed(tenant: str, message_id: str, content_hash: str) -> bool:
    tbl = _table()
    try:
        e = tbl.get_entity(tenant, _rk(message_id, content_hash))
        return e is not None
    except Exception:
        return False

def mark_stage(tenant: str, message_id: str, content_hash: str, stage: str, note: Optional[str] = None):
    tbl = _table()
    entity = {
        "PartitionKey": tenant,
        "RowKey": _rk(message_id, content_hash),
        "messageId": message_id,
        "hash": content_hash,
        "stage": stage,
        "note": note or "",
        "ts": int(time.time())
    }
    tbl.upsert_entity(entity=entity, mode=UpdateMode.MERGE)
