import json, logging, base64
from app.config import settings
from app.mr_sign import sign_mr, SigningError
from app.hacienda import post_recepcion, poll_estado
from app.storage_io import save_mr, save_response
from app.idempotency import mark_stage

def main(msg: str):
    """
    Mensaje de entrada:
      {
        "tenant":..., "message_id":..., "clave":..., "mr_xml_b64":...,
        "consRec":..., "emisor_id":..., "receptor_id":..., "fecha":...
      }
    Firma XAdES-EPES con Key Vault, envía a /recepcion y hace polling.
    Guarda MR firmado y respuestas.
    """
    payload = json.loads(msg)
    tenant = payload["tenant"]
    message_id = payload["message_id"]
    clave = payload["clave"]
    cons_rec = payload["consRec"]
    emisor_id = payload["emisor_id"]
    receptor_id = payload["receptor_id"]
    fecha = payload["fecha"]
    mr_xml = base64.b64decode(payload["mr_xml_b64"])

    try:
        # Firmar MR (XAdES-EPES con KV)
        s = sign_mr(mr_xml)
        save_mr(tenant, clave, s.signed_xml, cons_rec, signed=True,
                tags={"tenant": tenant, "clave": clave, "consRec": cons_rec})

        # Enviar a Hacienda
        resp = post_recepcion(
            signed_xml=s.signed_xml,
            clave=clave,
            fecha_rfc3339=fecha,
            emisor_id=emisor_id,
            receptor_id=receptor_id
        )
        # Guardar respuesta inicial (puede traer Location)
        initial_payload = json.dumps({
            "status_code": resp.status_code,
            "body": resp.body,
            "location": resp.location,
            "rate_limit": resp.rate_limit
        }).encode("utf-8")
        save_response(tenant, clave, initial_payload, is_json=True,
                      tags={"tenant": tenant, "clave": clave})

        # Polling si hay Location
        if resp.location:
            estado, final_body = poll_estado(resp.location, max_wait=180, base_interval=5)
            final_payload = json.dumps({"estado": estado, "body": final_body}).encode("utf-8")
            save_response(tenant, clave, final_payload, is_json=True,
                          tags={"tenant": tenant, "clave": clave, "estado": estado})

        mark_stage(tenant, message_id, clave, "done", f"cons={cons_rec}")

    except SigningError as se:
        logging.exception("Firma XAdES error: %s", se)
        # si querés, podrías mandar a quarantine el MR sin firmar, pero aquí ya venía validado
        raise
    except Exception as e:
        logging.exception("build_and_sign error: %s", e)
        raise
