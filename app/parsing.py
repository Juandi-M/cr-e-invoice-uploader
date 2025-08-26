"""
Validación/parseo de factura: carga XSD (si hay), valida y extrae metadatos.
Compatibilidad básica con FE/TE/NC/ND (buscar campos típicos).
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from lxml import etree
from app.config import settings

class InvoiceValidationError(Exception):
    pass

@dataclass
class InvoiceMeta:
    tenant: str
    message_id: str
    filename: str
    clave: str
    consecutivo: str | None
    ced_emisor: str | None
    ced_receptor: str | None
    total: float | None

def _load_schema(xsd_path: str) -> Optional[etree.XMLSchema]:
    if not xsd_path:
        return None
    with open(xsd_path, "rb") as f:
        schema_doc = etree.parse(f)
    return etree.XMLSchema(schema_doc)

def _to_float_or_none(text: str | None) -> float | None:
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None

def _extract(root: etree._Element) -> Tuple[str, str | None, str | None, str | None, float | None]:
    # Campos comunes en múltiples tipos de comprobante
    clave = (root.findtext(".//Clave") or "").strip()
    consecutivo = (root.findtext(".//NumeroConsecutivo") or "").strip() or None

    # Cédulas (varían por tipo/modelo)
    ced_emisor = root.findtext(".//Emisor/Identificacion/Numero") or root.findtext(".//Emisor/NumeroIdentificacion")
    ced_receptor = root.findtext(".//Receptor/Identificacion/Numero") or root.findtext(".//Receptor/NumeroIdentificacion")
    ced_emisor = ced_emisor.strip() if ced_emisor else None
    ced_receptor = ced_receptor.strip() if ced_receptor else None

    # Total
    total = root.findtext(".//ResumenFactura/TotalComprobante") or root.findtext(".//TotalFactura") or root.findtext(".//TotalComprobante")
    return clave, consecutivo, ced_emisor, ced_receptor, _to_float_or_none(total)

def validate_and_extract(xml_bytes: bytes, tenant: str, message_id: str, filename: str) -> InvoiceMeta:
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        doc = etree.fromstring(xml_bytes, parser=parser)
    except etree.XMLSyntaxError as e:
        raise InvoiceValidationError(f"XML mal formado: {e}") from e

    # Si config trae XSD, valida
    schema = _load_schema(settings.inv_xsd_path)
    if schema:
        try:
            schema.assertValid(doc)
        except etree.DocumentInvalid as e:
            raise InvoiceValidationError(f"Violación XSD: {e}") from e

    clave, consecutivo, ced_emisor, ced_receptor, total = _extract(doc)
    if not clave:
        raise InvoiceValidationError("Falta <Clave> en el comprobante.")
    return InvoiceMeta(
        tenant=tenant,
        message_id=message_id,
        filename=filename,
        clave=clave,
        consecutivo=consecutivo,
        ced_emisor=ced_emisor,
        ced_receptor=ced_receptor,
        total=total,
    )
