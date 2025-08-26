from dataclasses import dataclass
from typing import Tuple
from azure.data.tables import TableServiceClient, UpdateMode
from app.config import settings

TABLE = "consecutivos"

@dataclass(frozen=True)
class Serie:
    cedula: str
    sucursal: str = "001"
    terminal: str = "00001"
    dd: str = "05"  # una sola serie para MR; el estado viaja en <Mensaje>

def _table():
    svc = TableServiceClient.from_connection_string(settings.storage_conn)
    try:
        svc.create_table(TABLE)
    except Exception:
        pass
    return svc.get_table_client(TABLE)

def next_consecutivo(serie: Serie) -> Tuple[str, int]:
    """
    Devuelve (consecutivo20, n) con incremento atómico por serie.
    PK = cedula|sucursal|terminal|dd ; RK = 'seq'
    """
    tbl = _table()
    pk = f"{serie.cedula}|{serie.sucursal}|{serie.terminal}|{serie.dd}"
    rk = "seq"
    try:
        row = tbl.get_entity(pk, rk)
        n = int(row.get("n", 0)) + 1
        row["n"] = n
        tbl.update_entity(entity=row, mode=UpdateMode.REPLACE)
    except Exception:
        n = 1
        tbl.upsert_entity({"PartitionKey": pk, "RowKey": rk, "n": n})
    consec = f"{serie.sucursal}{serie.terminal}{serie.dd}{n:010d}"
    return consec, n
