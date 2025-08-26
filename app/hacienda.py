from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import base64, time, requests, logging, json
from app.config import settings
from app.rate_limit import sleep_from_headers

REQ_TIMEOUT = (10, 30)

class HaciendaError(Exception): pass

@dataclass
class HaciendaResponse:
    ok: bool
    status_code: int
    body: dict | str
    location: Optional[str]
    rate_limit: Optional[Tuple[str | None, str | None]]

def _token() -> str:
    data = {
        "grant_type": "password",
        "client_id": settings.idp_client_id,
        "username": settings.idp_username,
        "password": settings.idp_password,
    }
    r = requests.post(settings.idp_token_url, data=data, timeout=REQ_TIMEOUT)
    if r.status_code != 200:
        raise HaciendaError(f"Token error {r.status_code}: {r.text}")
    tok = r.json().get("access_token")
    if not tok:
        raise HaciendaError("Token response sin access_token")
    return tok

def post_recepcion(signed_xml: bytes, *, clave: str, fecha_rfc3339: str,
                   emisor_id: str, receptor_id: str, callback_url: Optional[str]=None) -> HaciendaResponse:
    token = _token()
    payload = {
        "clave": clave,
        "fecha": fecha_rfc3339,
        "emisor": {"numeroIdentificacion": emisor_id},
        "receptor": {"numeroIdentificacion": receptor_id},
        "comprobanteXml": base64.b64encode(signed_xml).decode("ascii"),
    }
    if callback_url:
        payload["callbackUrl"] = callback_url
    url = f"{settings.recepcion_base_url}/recepcion"
    r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=REQ_TIMEOUT)

    loc = r.headers.get("Location")
    rl = (r.headers.get("X-Ratelimit-Limit"), r.headers.get("X-Ratelimit-Remaining"))
    body: dict | str
    try:
        body = r.json()
    except Exception:
        body = r.text or ""
    return HaciendaResponse(ok=r.status_code in (200,201,202), status_code=r.status_code, body=body, location=loc, rate_limit=rl)

def poll_estado(location_url: str, *, max_wait: int = 180, base_interval: int = 5) -> Tuple[str, dict]:
    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
    waited = 0
    while waited <= max_wait:
        r = requests.get(location_url, headers=headers, timeout=REQ_TIMEOUT)
        if r.status_code == 200:
            try:
                body = r.json()
            except Exception:
                body = {}
            estado = (body.get("ind-estado") or body.get("ind_estado") or "").lower()
            if estado in ("aceptado", "rechazado", "aceptadoparcial"):
                return estado, body
        slept = sleep_from_headers(r.headers, default_interval=base_interval)
        waited += slept
    return "timeout", {}
