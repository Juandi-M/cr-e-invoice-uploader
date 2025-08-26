"""
Cliente Hacienda:
 - Token ROPC (Keycloak)
 - POST /recepcion (comprobanteXml base64)
 - Leer Location y hacer poll con backoff (rate limit aware)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
from app.config import settings
import base64, logging, time, requests

REQ_TIMEOUT = (10, 30)  # connect, read

class HaciendaError(Exception):
    pass

@dataclass
class HaciendaResponse:
    ok: bool
    status_code: int
    body: dict | str
    location: str | None
    rate_limit: Tuple[str | None, str | None] | None

def _get_token() -> str:
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

def send_recepcion_xml_signed(signed_xml: bytes, *, clave: str, fecha_rfc3339: str,
                              emisor_id: str, receptor_id: str,
                              callback_url: Optional[str] = None) -> HaciendaResponse:
    token = _get_token()
    payload = {
        "clave": clave,
        "fecha": fecha_rfc3339,
        "emisor": {"numeroIdentificacion": emisor_id},
        "receptor": {"numeroIdentificacion": receptor_id},
        "comprobanteXml": base64.b64encode(signed_xml).decode("ascii"),
    }
    if callback_url:
        payload["callbackUrl"] = callback_url  # soportado por el API

    url = f"{settings.recepcion_base_url}/recepcion"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=REQ_TIMEOUT)

    location = r.headers.get("Location")
    rl = (r.headers.get("X-Ratelimit-Limit"), r.headers.get("X-Ratelimit-Remaining"))
    if r.status_code not in (200, 201, 202):
        return HaciendaResponse(False, r.status_code, r.text, location, rl)

    body: dict | str
    try:
        body = r.json()
    except Exception:
        body = r.text or ""

    return HaciendaResponse(True, r.status_code, body, location, rl)

def poll_estado(location_url: str, *, max_wait_sec: int = 180, interval_sec: int = 5) -> Tuple[str, dict]:
    """
    Devuelve (estado, body_json)
      estado in ["aceptado","rechazado","procesando","aceptadoparcial","timeout","error"]
    """
    start = time.time()
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}

    while True:
        r = requests.get(location_url, headers=headers, timeout=REQ_TIMEOUT)
        if r.status_code == 200:
            try:
                body = r.json()
            except Exception:
                body = {}
            estado = (body.get("ind-estado") or body.get("ind_estado") or "").lower()
            if estado in ("aceptado", "rechazado", "procesando", "aceptadoparcial"):
                return estado, body

        # Manejo simple de rate limit (si viene el header)
        remaining = r.headers.get("X-Ratelimit-Remaining")
        if remaining is not None and remaining.isdigit() and int(remaining) == 0:
            reset = r.headers.get("X-Ratelimit-Reset")
            sleep_for = int(reset) if (reset and reset.isdigit()) else interval_sec
        else:
            sleep_for = interval_sec

        if time.time() - start + sleep_for > max_wait_sec:
            return "timeout", {}

        time.sleep(sleep_for)
