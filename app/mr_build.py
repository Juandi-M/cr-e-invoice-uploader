from dataclasses import dataclass
from typing import Optional
from lxml import etree
from app.xsd import mr_schema
from app.config import settings

NS_MR = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeReceptor"

@dataclass
class MRInput:
    clave: str
    numero_cedula_emisor: str
    fecha_emision_doc: str           # RFC3339Z
    mensaje: int                     # 1/2/3
    detalle_mensaje: Optional[str]
    monto_total_impuesto: Optional[float]
    total_factura: Optional[float]
    numero_cedula_receptor: str
    numero_consecutivo_receptor: str

def build_mr_xml(inp: MRInput) -> bytes:
    root = etree.Element("{%s}MensajeReceptor" % NS_MR, nsmap={None: NS_MR})
    def add(tag, text):
        el = etree.SubElement(root, tag); el.text = text; return el

    add("Clave", inp.clave)
    add("NumeroCedulaEmisor", inp.numero_cedula_emisor)
    add("FechaEmisionDoc", inp.fecha_emision_doc)
    add("Mensaje", str(inp.mensaje))
    if inp.detalle_mensaje:
        add("DetalleMensaje", inp.detalle_mensaje)
    if inp.monto_total_impuesto is not None:
        add("MontoTotalImpuesto", f"{inp.monto_total_impuesto:.5f}")
    if inp.total_factura is not None:
        add("TotalFactura", f"{inp.total_factura:.5f}")
    add("NumeroCedulaReceptor", inp.numero_cedula_receptor)
    add("NumeroConsecutivoReceptor", inp.numero_consecutivo_receptor)

    xml_bytes = etree.tostring(root, encoding="UTF-8", xml_declaration=True)

    # Validación MR contra XSD oficial (v4.4)
    mr_s = mr_schema(settings.mr_xsd_path)
    mr_s.assertValid(etree.fromstring(xml_bytes))

    return xml_bytes
