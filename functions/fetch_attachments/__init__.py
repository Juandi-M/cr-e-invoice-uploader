import json, logging, base64
from azure.storage.queue import QueueClient
from app.config import settings
from app.graph import fetch_invoice_attachments
from app.storage_io import save_raw_invoice
from app.idempotency import sha256, already_processed, mark_stage

def _q(name: str) -> QueueClient:
    return QueueClient.from_connection_string(settings.storage_conn, name)

def main(msg: str):
    """
    Mensaje de entrada: {"tenant": "...", "message_id": "..."}
    Descarga adjuntos XML, guarda crudo en Blob y encola a validate.
    """
    try:
        payload = json.loads(msg)
        tenant = payload["tenant"]
        message_id = payload["message_id"]

        atts = fetch_invoice_attachments(message_id, user_id=None)
        if not atts:
            logging.warning("No hay adjuntos XML en message_id=%s", message_id)
            return

        for (filename, xml_bytes) in atts:
            h = sha256(xml_bytes)
            if already_processed(tenant, message_id, h):
                logging.info("Duplicado saltado (idempotency): %s", filename)
                continue

            # Guardar XML crudo
            tags = {"tenant": tenant, "message_id": message_id, "hash": h}
            try:
                # Intentamos extraer "Clave" para nombrar; si falla, usa filename
                clave_guess = filename.rsplit(".", 1)[0]
                save_raw_invoice(tenant, clave_guess, xml_bytes, tags)
            except Exception:
                # fallback: igual seguimos
                pass

            # Encolar a validate con el XML embebido (base64)
            vmsg = {
                "tenant": tenant,
                "message_id": message_id,
                "filename": filename,
                "xml_b64": base64.b64encode(xml_bytes).decode("ascii"),
                "hash": h
            }
            _q(settings.q_validate).send_message(json.dumps(vmsg))
            mark_stage(tenant, message_id, h, "queued-validate", filename)

    except Exception as e:
        logging.exception("fetch_attachments error: %s", e)
        raise
