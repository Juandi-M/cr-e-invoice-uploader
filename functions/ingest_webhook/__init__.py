import json
import logging
import azure.functions as func
from azure.storage.queue import QueueClient
from app.config import settings
from app.storage_io import ensure_containers

def _q(name: str) -> QueueClient:
    return QueueClient.from_connection_string(settings.storage_conn, name)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        ensure_containers()

        body = req.get_json()
        tenant = body.get("tenant") or settings.tenant_id
        message_id = body["message_id"]   # ID del correo/mensaje origen (Graph u otro)
        meta = {
            "tenant": tenant,
            "message_id": message_id
        }

        _q(settings.q_incoming).send_message(json.dumps(meta))
        return func.HttpResponse(
            json.dumps({"ok": True, "queued": meta}),
            status_code=202,
            mimetype="application/json"
        )
    except Exception as e:
        logging.exception("ingest_webhook error")
        return func.HttpResponse(
            json.dumps({"ok": False, "error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
