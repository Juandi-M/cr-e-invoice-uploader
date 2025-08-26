# app/storage_io.py
from __future__ import annotations
from typing import Dict, Optional
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient, ContentSettings
from app.config import settings

_blob = BlobServiceClient.from_connection_string(settings.storage_conn)

def ensure_containers():
    for name in (settings.blob_raw, "mr", "signed", "responses", settings.blob_quar):
        try:
            _blob.create_container(name)
        except Exception:
            pass  # ya existe

def _upload_bytes(container: str, blob_path: str, data: bytes,
                  tags: Optional[Dict[str, str]] = None,
                  content_type: str = "application/xml") -> str:
    bc = _blob.get_blob_client(container, blob_path)
    bc.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )
    if tags:
        # Nota: requiere Blob Index habilitado en la cuenta
        try:
            bc.set_blob_tags(tags)
        except Exception:
            pass
    return bc.url

def save_raw_invoice(tenant: str, clave: str, xml: bytes, tags: Dict[str, str]) -> str:
    dt = datetime.now(timezone.utc)
    path = f"{tenant}/{dt:%Y/%m/%d}/{clave}.xml"
    return _upload_bytes(settings.blob_raw, path, xml, tags)

def save_mr(tenant: str, clave: str, xml: bytes, consecutivo: str, signed: bool, tags: Dict[str, str]) -> str:
    dt = datetime.now(timezone.utc)
    suffix = "mr-signed.xml" if signed else "mr.xml"
    path = f"{tenant}/{dt:%Y/%m/%d}/{clave}-{suffix}"
    return _upload_bytes("signed" if signed else "mr", path, xml, tags)

def save_hacienda_response(tenant: str, clave: str, payload: bytes, content_type: str, tags: Dict[str, str]) -> str:
    dt = datetime.now(timezone.utc)
    path = f"{tenant}/{dt:%Y/%m/%d}/{clave}.{'json' if content_type=='application/json' else 'xml'}"
    return _upload_bytes("responses", path, payload, tags, content_type=content_type)

def save_quarantine(tenant: str, name: str, xml: bytes, tags: Dict[str, str]) -> str:
    dt = datetime.now(timezone.utc)
    path = f"{tenant}/{dt:%Y/%m/%d}/{name}"
    return _upload_bytes(settings.blob_quar, path, xml, tags)
