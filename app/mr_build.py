"""
Construcción de Mensaje Receptor (v4.4).
Mensaje: 1=aceptado, 2=aceptado parcial, 3=rechazado.
XSD opcional via settings.mr_xsd_path.
"""
from dataclasses import dataclass
from typing import Optional
from lxml import etree
from app.config import settings

NS_MR = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeReceptor"

@dataclass
class MRInput:
    clave: str
    numero_cedula_emisor: str
    fecha_emision_doc: str          # RFC3339Z
    mensaje: int                    # 1|2|3
    detalle_mensaje: Optional[str]  # texto libre
    monto_total_impuesto: Optional[float]
    total_factura: Optional[float]
    numero_cedula_receptor: str
    consecutivo_receptor: str

def build_mr_xml(inp: MRInput) -> bytes:
    root = etree.Element("{%s}MensajeReceptor" % NS_MR, nsmap={None: NS_MR})

    def _add(tag, text):
        el = etree.SubElement(root, tag)
        el.text = text
        return el

    _add("Clave", inp.clave)
    _add("NumeroCedulaEmisor", inp.numero_cedula_emisor)
    _add("FechaEmisionDoc", inp.fecha_emision_doc)
    _add("Mensaje", str(inp.mensaje))
    if inp.detalle_mensaje:
        _add("DetalleMensaje", inp.detalle_mensaje)

    if inp.monto_total_impuesto is not None:
        _add("MontoTotalImpuesto", f"{inp.monto_total_impuesto:.5f}")

    if inp.total_factura is not None:
        _add("TotalFactura", f"{inp.total_factura:.5f}")

    _add("NumeroCedulaReceptor", inp.numero_cedula_receptor)
    _add("NumeroConsecutivoReceptor", inp.consecutivo_receptor)

    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)

    # Validación XSD (opcional)
    if settings.mr_xsd_path:
        with open(settings.mr_xsd_path, "rb") as f:
            schema = etree.XMLSchema(etree.parse(f))
        schema.assertValid(etree.fromstring(xml_bytes))

    return xml_bytes
