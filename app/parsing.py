from dataclasses import dataclass
from typing import Optional
from lxml import etree
from app.xsd import validate_xml, invoice_schema
from app.config import settings

class InvoiceValidationError(Exception):
    pass

@dataclass
class InvoiceMeta:
    tenant: str
    message_id: str
    filename: str
    clave: str
    consecutivo: Optional[str]
    ced_emisor: Optional[str]
    ced_receptor: Optional[str]
    total: Optional[float]

def _to_float(x: Optional[str]) -> Optional[float]:
    if not x: return None
    try:
        return float(x)
    except Exception:
        return None

def validate_and_extract(xml_bytes: bytes, tenant: str, message_id: str, filename: str) -> InvoiceMeta:
    # 1) Validación XSD oficial (v4.4) — siempre
    schema = invoice_schema(settings.inv_xsd_path)
    try:
        validate_xml(xml_bytes, schema)
    except Exception as e:
        raise InvoiceValidationError(f"Violación XSD Factura: {e}") from e

    # 2) Parseo/Extracción
    root = etree.fromstring(xml_bytes)
    clave = (root.findtext(".//Clave") or "").strip()
    if not clave:
        raise InvoiceValidationError("Falta <Clave> en factura.")

    consecutivo = (root.findtext(".//NumeroConsecutivo") or "").strip() or None
    ced_emisor = (root.findtext(".//Emisor/Identificacion/Numero")
                  or root.findtext(".//Emisor/NumeroIdentificacion") or "")
    ced_receptor = (root.findtext(".//Receptor/Identificacion/Numero")
                    or root.findtext(".//Receptor/NumeroIdentificacion") or "")
    total = (root.findtext(".//ResumenFactura/TotalComprobante")
             or root.findtext(".//TotalComprobante") or "")

    return InvoiceMeta(
        tenant=tenant, message_id=message_id, filename=filename,
        clave=clave,
        consecutivo=consecutivo,
        ced_emisor=ced_emisor.strip() or None,
        ced_receptor=ced_receptor.strip() or None,
        total=_to_float(total.strip())
    )
