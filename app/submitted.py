# app/submitted.py
from azure.data.tables import TableServiceClient, UpdateMode
from app.config import settings

TABLE = "submitted"

def _table():
    svc = TableServiceClient.from_connection_string(settings.storage_conn)
    try:
        svc.create_table(TABLE)
    except Exception:
        pass
    return svc.get_table_client(TABLE)

def was_submitted(tenant: str, clave: str) -> bool:
    t = _table()
    try:
        t.get_entity(tenant, clave)
        return True
    except Exception:
        return False

def mark_submitted(tenant: str, clave: str, estado: str):
    t = _table()
    ent = {"PartitionKey": tenant, "RowKey": clave, "estado": estado}
    t.upsert_entity(ent, mode=UpdateMode.MERGE)
