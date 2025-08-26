from typing import List, Tuple
import base64, requests
from app.config import settings
import msal

GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_API = "https://graph.microsoft.com/v1.0"

class GraphError(Exception): pass

def _token() -> str:
    app = msal.ConfidentialClientApplication(
        settings.graph_client_id,
        authority=f"https://login.microsoftonline.com/{settings.graph_tenant_id}",
        client_credential=settings.graph_client_secret,
    )
    res = app.acquire_token_silent(GRAPH_SCOPE, account=None) or app.acquire_token_for_client(GRAPH_SCOPE)
    if "access_token" not in res: raise GraphError(res.get("error_description"))
    return res["access_token"]

def fetch_invoice_attachments(message_id: str, user_id: str | None = None) -> List[Tuple[str, bytes]]:
    user = user_id or settings.graph_user_id
    tok = _token()
    url = f"{GRAPH_API}/users/{user}/messages/{message_id}/attachments?$select=name,contentType,contentBytes"
    r = requests.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    if r.status_code != 200:
        raise GraphError(f"GET attachments {r.status_code}: {r.text}")
    out: List[Tuple[str, bytes]] = []
    for att in r.json().get("value", []):
        name = att.get("name","")
        ctype = att.get("contentType","")
        if ctype in ("text/xml","application/xml") or name.lower().endswith(".xml"):
            out.append((name, base64.b64decode(att.get("contentBytes",""))))
    return out
