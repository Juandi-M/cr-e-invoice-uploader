import json, base64, logging, re
from datetime import datetime, timedelta, timezone
import azure.functions as func
from azure.storage.queue import QueueClient
from lxml import etree

from app.config import settings
from app.graph import list_messages_with_attachments_since, fetch_invoice_attachments
from app.idempotency import sha256, already_processed, mark_stage
from app.submitted import was_submitted
from app.storage_io import ensure_containers

def _q(name: str) -> QueueClient:
    return QueueClient.from_connection_string(settings.storage_conn, name)

RE_50 = re.compile(rb"<\s*Clave\s*>\s*(\d{50})\s*<\s*/\s*Clave\s*>")
TENANT = settings.tenant_id.encode()
ROOTS = {b"FacturaElectronica", b"TiqueteElectronico", b"FacturaElectronicaCompra",
         b"NotaCreditoElectronica", b"NotaDebitoElectronica", b"FacturaElectronicaExportacion"}

def _is_probably_cr_invoice(xml: bytes) -> tuple[bool, str|None]:
    try:
        root = etree.fromstring(xml)
        ln = etree.QName(root.tag).localname.encode()
        if ln not in ROOTS:
            return False, None
        m = RE_50.search(xml)
        if not m:
            return False, None
        clave = m.group(1).decode()
        rec_num = (root.findtext(".//Receptor/Identificacion/Numero")
                   or root.findtext(".//Receptor/NumeroIdentificacion") or "")
        if rec_num.strip().encode() != TENANT:
            return False, None
        return True, clave
    except Exception:
        return False, None

def main(myTimer: func.TimerRequest) -> None:
    ensure_containers()

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    logging.info("weekly_scan window since %s", since)

    messages = list_messages_with_attachments_since(since)
    if not messages:
        logging.info("weekly_scan: no messages with attachments in window")
        return

    for m in messages:
        mid = m["id"]
        atts = fetch_invoice_attachments(mid)
        if not atts:
            continue
        for (filename, xml_bytes) in atts:
            ok, clave = _is_probably_cr_invoice(xml_bytes)
            if not ok or not clave:
                continue
            # dedupe por Clave global
            if was_submitted(settings.tenant_id, clave):
                logging.info("weekly_scan: clave ya procesada %s", clave)
                continue

            # dedupe por hash por mensaje (idempotency existente)
            h = sha256(xml_bytes)
            if already_processed(settings.tenant_id, mid, h):
                logging.info("weekly_scan: hash ya procesado para message %s", mid)
                continue

            vmsg = {
                "tenant": settings.tenant_id,
                "message_id": mid,
                "filename": filename,
                "xml_b64": base64.b64encode(xml_bytes).decode("ascii"),
                "hash": h
            }
            _q(settings.q_validate).send_message(json.dumps(vmsg))
            mark_stage(settings.tenant_id, mid, h, "queued-validate", filename)
