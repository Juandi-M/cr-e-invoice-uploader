# app/consecutivo.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from azure.data.tables import TableServiceClient, UpdateMode
from app.config import settings

TABLE = "consecutivos"

@dataclass(frozen=True)
class Serie:
    cedula: str
    sucursal: str = "001"   # fijo para simplificar
    terminal: str = "00001" # fijo para simplificar
    dd: str = "05"          # única serie para todos los MR; estado va en <Mensaje>

def _table():
    svc = TableServiceClient.from_connection_string(settings.storage_conn)
    try:
        svc.create_table(TABLE)
    except Exception:
        pass
    return svc.get_table_client(TABLE)

def next_consecutivo(serie: Serie) -> Tuple[str, int]:
    """
    Retorna (consecutivo20, n) garantizando incremento atómico por serie:
    PK = cedula|sucursal|terminal|dd ; RK = 'seq'
    """
    tbl = _table()
    pk = f"{serie.cedula}|{serie.sucursal}|{serie.terminal}|{serie.dd}"
    rk = "seq"

    try:
        row = tbl.get_entity(pk, rk)
        n = int(row.get("n", 0)) + 1
        row["n"] = n
        tbl.update_entity(mode=UpdateMode.REPLACE, entity=row)
    except Exception:
        # primera vez
        n = 1
        tbl.upsert_entity({"PartitionKey": pk, "RowKey": rk, "n": n})

    # Formato 20 dígitos: SSS TTTTT DD NNNNNNNNNN
    consec = f"{serie.sucursal}{serie.terminal}{serie.dd}{n:010d}"
    return consec, n
