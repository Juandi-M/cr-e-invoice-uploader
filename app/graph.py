"""
Microsoft Graph helpers — descarga adjuntos XML por messageId.
App Perms (client credentials). Requiere consentimiento en Graph:
  - Mail.Read (Application)
"""
from typing import List, Tuple
import logging, base64, requests
from app.config import settings
import msal

GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_API = "https://graph.microsoft.com/v1.0"

class GraphError(Exception):
    pass

def _get_graph_token() -> str:
    app = msal.ConfidentialClientApplication(
        settings.graph_client_id,
        authority=f"https://login.microsoftonline.com/{settings.graph_tenant_id}",
        client_credential=settings.graph_client_secret,
    )
    result = app.acquire_token_silent(GRAPH_SCOPE, account=None)
    if not result:
        result = app.acquire_token_for_client(GRAPH_SCOPE)
    if "access_token" not in result:
        raise GraphError(f"MSAL error: {result.get('error')} {result.get('error_description')}")
    return result["access_token"]

def fetch_invoice_attachments(message_id: str, user_id: str | None = None) -> List[Tuple[str, bytes]]:
    """
    Devuelve [(filename, bytes)] de adjuntos XML en un mensaje.
    user_id: UPN/GUID del buzón (default: settings.graph_user_id).
    """
    user = user_id or settings.graph_user_id
    token = _get_graph_token()
    url = f"{GRAPH_API}/users/{user}/messages/{message_id}/attachments?$select=name,contentType,contentBytes"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    if r.status_code != 200:
        raise GraphError(f"GET attachments {r.status_code}: {r.text}")
    data = r.json()
    out: List[Tuple[str, bytes]] = []
    for item in data.get("value", []):
        ctype = item.get("contentType", "")
        name = item.get("name", "")
        if ctype in ("text/xml", "application/xml") or name.lower().endswith(".xml"):
            b64 = item.get("contentBytes")
            if b64:
                out.append((name, base64.b64decode(b64)))
    logging.info("Graph: %d XML attachment(s) fetched for message=%s", len(out), message_id)
    return out
