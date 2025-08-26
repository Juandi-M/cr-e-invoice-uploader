# app/graph.py
import os
import time
import logging
import base64
import requests
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timezone
from app.config import settings

GRAPH_TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# Env vars esperadas (delegated)
# GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, GRAPH_REFRESH_TOKEN
CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("GRAPH_REFRESH_TOKEN", "")

SCOPES = "https://graph.microsoft.com/.default offline_access openid profile Mail.Read"

class GraphError(Exception): pass

_token_cache: Dict[str, any] = {}

def _now() -> int:
    return int(time.time())

def _get_access_token() -> str:
    """
    Intercambia el REFRESH_TOKEN por un ACCESS TOKEN (delegated) para Outlook.com (consumers).
    """
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise GraphError("Faltan GRAPH_CLIENT_ID / GRAPH_CLIENT_SECRET / GRAPH_REFRESH_TOKEN (delegated).")

    # usa cache corto si no expira
    if _token_cache.get("access_token") and _token_cache.get("exp") and _token_cache["exp"] > _now() + 60:
        return _token_cache["access_token"]

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "scope": SCOPES,
    }
    resp = requests.post(GRAPH_TOKEN_URL, data=data, timeout=30)
    if resp.status_code != 200:
        raise GraphError(f"Token error {resp.status_code}: {resp.text}")
    tok = resp.json()
    at = tok["access_token"]
    _token_cache["access_token"] = at
    _token_cache["exp"] = _now() + int(tok.get("expires_in", 3600))
    # opcional: si Microsoft devolviera un nuevo refresh_token, podrías almacenarlo
    return at

def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {_get_access_token()}"}

def list_messages_with_attachments_since(since_iso: str, top: int = 50) -> List[Dict]:
    """
    Lista mensajes de la cuenta personal (delegated) desde "since_iso" (UTC) con adjuntos.
    Devuelve dicts con {id, subject, receivedDateTime, hasAttachments}
    """
    url = f"{GRAPH_BASE}/me/messages"
    # Filtro por fecha
    params = {
        "$select": "id,subject,receivedDateTime,hasAttachments",
        "$orderby": "receivedDateTime DESC",
        "$top": str(top),
        "$filter": f"receivedDateTime ge {since_iso}"
    }
    out = []
    while True:
        r = requests.get(url, headers=_headers(), params=params, timeout=30)
        if r.status_code != 200:
            raise GraphError(f"List messages error {r.status_code}: {r.text}")
        data = r.json()
        out.extend(data.get("value", []))
        nxt = data.get("@odata.nextLink")
        if not nxt:
            break
        url = nxt
        params = None  # nextLink ya incluye query
        if len(out) >= 500:
            break
    # filtra solo los que tienen adjuntos
    return [m for m in out if m.get("hasAttachments")]

def fetch_invoice_attachments(message_id: str) -> List[Tuple[str, bytes]]:
    """
    Devuelve lista de (filename, bytes) de adjuntos XML del mensaje.
    Sólo 'fileAttachment' con contentBytes.
    """
    url = f"{GRAPH_BASE}/me/messages/{message_id}/attachments"
    params = {"$select": "name,contentType,size,@odata.type,contentBytes"}
    r = requests.get(url, headers=_headers(), params=params, timeout=30)
    if r.status_code != 200:
        raise GraphError(f"List attachments error {r.status_code}: {r.text}")
    items = r.json().get("value", [])
    out: List[Tuple[str, bytes]] = []
    for it in items:
        if it.get("@odata.type") != "#microsoft.graph.fileAttachment":
            continue
        name = it.get("name") or "attachment"
        ctype = it.get("contentType") or ""
        if not (name.lower().endswith(".xml") or ctype == "application/xml" or ctype.endswith("+xml")):
            continue
        b64 = it.get("contentBytes")
        if not b64:
            continue
        out.append((name, base64.b64decode(b64)))
    return out
