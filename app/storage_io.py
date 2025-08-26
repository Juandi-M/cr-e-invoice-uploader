from typing import Dict, Optional
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient, ContentSettings
from app.config import settings

_blob = BlobServiceClient.from_connection_string(settings.storage_conn)

def ensure_containers():
    for name in {settings.blob_raw, settings.blob_mr, settings.blob_signed, settings.blob_resp, settings.blob_quar}:
        try: _blob.create_container(name)
        except Exception: pass

def _upload(container: str, path: str, data: bytes, content_type: str, tags: Optional[Dict[str,str]]=None) -> str:
    bc = _blob.get_blob_client(container, path)
    bc.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
    if tags:
        try: bc.set_blob_tags(tags)
        except Exception: pass
    return bc.url

def save_raw_invoice(tenant: str, clave: str, xml: bytes, tags: Dict[str,str]) -> str:
    dt = datetime.now(timezone.utc)
    path = f"{tenant}/{dt:%Y/%m/%d}/{clave}.xml"
    return _upload(settings.blob_raw, path, xml, "application/xml", tags)

def save_mr(tenant: str, clave: str, xml: bytes, consecutivo: str, signed: bool, tags: Dict[str,str]) -> str:
    dt = datetime.now(timezone.utc)
    suffix = "mr-signed.xml" if signed else "mr.xml"
    path = f"{tenant}/{dt:%Y/%m/%d}/{clave}-{suffix}"
    container = settings.blob_signed if signed else settings.blob_mr
    return _upload(container, path, xml, "application/xml", {**tags, "consRec": consecutivo})

def save_response(tenant: str, clave: str, payload: bytes, is_json: bool, tags: Dict[str,str]) -> str:
    dt = datetime.now(timezone.utc)
    ext = "json" if is_json else "xml"
    path = f"{tenant}/{dt:%Y/%m/%d}/{clave}.{ext}"
    ctype = "application/json" if is_json else "application/xml"
    return _upload(settings.blob_resp, path, payload, ctype, tags)

def save_quarantine(tenant: str, name: str, xml: bytes, tags: Dict[str,str]) -> str:
    dt = datetime.now(timezone.utc)
    path = f"{tenant}/{dt:%Y/%m/%d}/{name}"
    return _upload(settings.blob_quar, path, xml, "application/xml", tags)
