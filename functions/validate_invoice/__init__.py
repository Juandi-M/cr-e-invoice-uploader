import json, logging, base64
from datetime import datetime, timezone
from azure.storage.queue import QueueClient
from app.config import settings
from app.xsd import invoice_schema
from app.parsing import validate_and_extract, InvoiceValidationError
from app.storage_io import save_quarantine, save_mr
from app.consecutivo_recepcion import Serie, next_consecutivo
from app.mr_build import MRInput, build_mr_xml
from app.idempotency import mark_stage

def _q(name: str) -> QueueClient:
    return QueueClient.from_connection_string(settings.storage_conn, name)

def main(msg: str):
    """
    Mensaje de entrada:
      {
        "tenant":..., "message_id":..., "filename":..., "xml_b64":..., "hash":...
      }
    Valida contra XSD Factura, extrae metadatos y construye MR (sin firmar).
    Encola a 'q-sign'.
    """
    payload = json.loads(msg)
    tenant = payload["tenant"]
    message_id = payload["message_id"]
    filename = payload["filename"]
    xml_bytes = base64.b64decode(payload["xml_b64"])
    content_hash = payload["hash"]

    try:
        schema = invoice_schema(settings.inv_xsd_path)
        inv = validate_and_extract(xml_bytes, tenant, message_id, filename)

        # Generar consecutivo MR atómico (serie fija)
        serie = Serie(cedula=settings.tenant_id)
        cons20, _n = next_consecutivo(serie)

        # Construcción del MR (ACEPTADO por defecto: 1).
        # Si querés otra lógica (aceptado parcial / rechazo) la ajustamos acá.
        inp = MRInput(
            clave=inv.clave,
            numero_cedula_emisor=inv.ced_emisor or "",
            fecha_emision_doc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            mensaje=1,  # 1=aceptado (default)
            detalle_mensaje=None,
            monto_total_impuesto=None,  # opcional
            total_factura=inv.total,
            numero_cedula_receptor=settings.tenant_id,
            numero_consecutivo_receptor=cons20
        )

        mr_xml = build_mr_xml(inp)  # valida contra XSD MR internamente
        save_mr(tenant, inv.clave, mr_xml, cons20, signed=False,
                tags={"tenant": tenant, "clave": inv.clave, "consRec": cons20})

        smsg = {
            "tenant": tenant,
            "message_id": message_id,
            "clave": inv.clave,
            "mr_xml_b64": base64.b64encode(mr_xml).decode("ascii"),
            "consRec": cons20,
            "emisor_id": inp.numero_cedula_emisor,
            "receptor_id": inp.numero_cedula_receptor,
            "fecha": inp.fecha_emision_doc
        }
        _q(settings.q_sign).send_message(json.dumps(smsg))
        mark_stage(tenant, message_id, content_hash, "queued-sign", filename)

    except InvoiceValidationError as ve:
        logging.warning("XSD inválido: %s (%s)", filename, ve)
        save_quarantine(tenant, f"{filename}.invalid.xml", xml_bytes,
                        {"tenant": tenant, "error": "xsd_invalid"})
        raise
    except Exception as e:
        logging.exception("validate_invoice error: %s", e)
        raise
