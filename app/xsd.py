# app/xsd.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging, requests
from lxml import etree

# Rutas locales donde cacheamos los XSD
DEFAULT_DIR = Path("./xsd")

@dataclass
class XSDRefs:
    invoice_xsd_url: str     # URL oficial v4.4 Factura (o paquete .zip/pdf con anexo de XSDs)
    mr_xsd_url: str          # URL oficial v4.4 Mensaje Receptor
    invoice_xsd_path: Path = DEFAULT_DIR / "v4.4" / "FacturaElectronica_v4.4.xsd"
    mr_xsd_path: Path = DEFAULT_DIR / "v4.4" / "MensajeReceptor_v4.4.xsd"

def _download_if_missing(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    logging.info("Descargando XSD: %s -> %s", url, path)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    path.write_bytes(r.content)

def ensure_xsds(refs: XSDRefs) -> XSDRefs:
    _download_if_missing(refs.invoice_xsd_url, refs.invoice_xsd_path)
    _download_if_missing(refs.mr_xsd_url, refs.mr_xsd_path)
    return refs

def _schema_from(path: Path) -> etree.XMLSchema:
    with path.open("rb") as f:
        schema_doc = etree.parse(f)
    return etree.XMLSchema(schema_doc)

@dataclass
class Schemas:
    invoice: etree.XMLSchema
    mr: etree.XMLSchema

def load_schemas(invoice_xsd_path: Path, mr_xsd_path: Path) -> Schemas:
    return Schemas(
        invoice=_schema_from(invoice_xsd_path),
        mr=_schema_from(mr_xsd_path),
    )

def validate_xml(xml_bytes: bytes, schema: etree.XMLSchema) -> None:
    doc = etree.fromstring(xml_bytes)
    schema.assertValid(doc)  # lanza DocumentInvalid si no cumple
