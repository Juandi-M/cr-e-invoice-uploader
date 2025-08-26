"""
Firma del Mensaje Receptor como XMLDSig (enveloped, RSA-SHA256).
Backend PEM listo (xmlsec). Hook para Key Vault (RSA) — TODO.
Para XAdES-EPES: inyectar SignedProperties/Policy (pendiente según política usada).
"""
from dataclasses import dataclass
from lxml import etree
from app.config import settings
import logging

class SigningError(Exception):
    pass

@dataclass
class SignResult:
    signed_xml: bytes
    signature_method: str  # ej: rsa-sha256
    cert_thumbprint: str | None

# --- Backend PEM (xmlsec) ---
def _sign_with_pem(xml: bytes) -> SignResult:
    try:
        import xmlsec
    except Exception as e:
        raise SigningError("python-xmlsec no instalado/disponible.") from e

    parser = etree.XMLParser(remove_blank_text=True)
    doc = etree.fromstring(xml, parser)

    # Crear plantilla de firma
    sign_node = xmlsec.template.create(
        doc,
        xmlsec.Transform.EXCL_C14N,
        xmlsec.Transform.RSA_SHA256,
        ns="ds"
    )
    # Referencia al documento (enveloped)
    ref = xmlsec.template.add_reference(sign_node, xmlsec.Transform.SHA256, uri="")
    xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)
    xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)

    # KeyInfo + X509Data
    key_info = xmlsec.template.ensure_key_info(sign_node)
    x509 = xmlsec.template.add_x509_data(key_info)
    xmlsec.template.x509_data_add_certificate(x509)

    # Insertar firma como último hijo
    doc.append(sign_node)

    # Key Manager
    mngr = xmlsec.KeysManager()
    # Cargar key + cert
    key = xmlsec.Key.from_file(settings.pem_key_path, xmlsec.KeyFormat.PEM, password=settings.pem_key_password.encode() if settings.pem_key_password else None)
    key.load_cert_from_file(settings.pem_cert_path, xmlsec.KeyFormat.PEM)
    mngr.add_key(key)

    ctx = xmlsec.SignatureContext(mngr)
    ctx.sign(sign_node)

    # thumbprint opcional (si quieres calcular)
    thumb = None
    try:
        import hashlib
        with open(settings.pem_cert_path, "rb") as f:
            cert_pem = f.read()
        # hash del cert PEM (no del DER). Ajusta si quieres DER.
        thumb = hashlib.sha1(cert_pem).hexdigest().upper()
    except Exception:
        pass

    return SignResult(
        signed_xml=etree.tostring(doc, xml_declaration=True, encoding="UTF-8"),
        signature_method="rsa-sha256",
        cert_thumbprint=thumb
    )

# --- Backend Key Vault (hook, si deciden usar KV) ---
def _sign_with_keyvault(_xml: bytes) -> SignResult:
    # Implementar si quieres RS256 con CryptographyClient y construir XMLDSig manual:
    # 1) Construir SignedInfo (C14N) + DigestRefs
    # 2) Pedir firma KV (RSASSA-PKCS1v15 SHA-256)
    # 3) Inyectar <ds:SignatureValue> y <ds:KeyInfo>
    raise SigningError("KEYVAULT backend no implementado aún. Usa PEM o pide que lo integre.")

def sign_mr(xml_bytes: bytes) -> SignResult:
    if settings.sign_backend.upper() == "PEM":
        logging.info("Firmando MR con backend=PEM")
        return _sign_with_pem(xml_bytes)
    elif settings.sign_backend.upper() == "KEYVAULT":
        logging.info("Firmando MR con backend=KEYVAULT")
        return _sign_with_keyvault(xml_bytes)
    else:
        raise SigningError(f"Backend de firma desconocido: {settings.sign_backend}")
