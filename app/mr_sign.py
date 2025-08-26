"""
Firma XAdES-EPES del Mensaje Receptor usando Azure Key Vault (RSASSA-PKCS1v15/SHA-256).

Incluye:
 - ds:Signature (enveloped)
 - Referencia al documento (enveloped + exc-c14n)
 - QualifyingProperties con SignedProperties (SigningTime, SigningCertificate, SignaturePolicyIdentifier)
 - Referencia a SignedProperties (Type="http://uri.etsi.org/01903#SignedProperties")
 - ds:KeyInfo con X509Certificate del certificado de la llave en KV

Requiere:
  - Managed Identity con permiso "crypto sign" sobre la key
  - settings.kv_key_id (Key ID) y settings.kv_cert_id (Certificate ID) configurados
  - settings.sign_policy_uri / settings.sign_policy_hash_b64 / settings.sign_policy_hash_alg

Dependencias: azure-identity, azure-keyvault-keys, azure-keyvault-certificates, lxml, cryptography
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from lxml import etree
import base64, hashlib

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from azure.identity import DefaultAzureCredential
from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm
from azure.keyvault.certificates import CertificateClient

from app.config import settings

DS = "http://www.w3.org/2000/09/xmldsig#"
XADES = "http://uri.etsi.org/01903/v1.3.2#"

class SigningError(Exception): pass

@dataclass
class SignResult:
    signed_xml: bytes
    signature_method: str
    key_id: str

def _c14n(elem: etree._Element) -> bytes:
    # Exclusive C14N sin comentarios
    return etree.tostring(elem, method="c14n", exclusive=True, with_comments=False)

def _doc_digest(root: etree._Element) -> bytes:
    # Digest del documento (enveloped + exc-c14n)
    canon = _c14n(root)
    return hashlib.sha256(canon).digest()

def _load_cert_der_from_kv() -> bytes:
    if not settings.kv_cert_id or not settings.kv_url:
        raise SigningError("Key Vault Certificate no configurado (CR_FE_KV_URL / CR_FE_KV_CERT_ID).")
    cred = DefaultAzureCredential()
    cert_client = CertificateClient(vault_url=settings.kv_url, credential=cred)
    # kv_cert_id puede ser URL completa; extraemos el nombre
    # https://.../certificates/<name>/<version>
    parts = settings.kv_cert_id.strip("/").split("/")
    try:
        idx = parts.index("certificates")
        name = parts[idx+1]
        # Si trae versión, get_certificate la ignora y trae la actual; para versión fija usa get_certificate_version
        cert = cert_client.get_certificate(name)
    except Exception as e:
        raise SigningError(f"No se pudo obtener certificado desde Key Vault: {e}") from e
    if not cert.cer:
        raise SigningError("El certificado en Key Vault no contiene blob DER (.cer)")
    return cert.cer  # DER bytes

def _x509_fields_from_der(der: bytes):
    cert = x509.load_der_x509_certificate(der)
    issuer = cert.issuer.rfc4514_string()
    serial = cert.serial_number
    return issuer, serial

def sign_mr(xml_bytes: bytes) -> SignResult:
    if not settings.kv_key_id or not settings.kv_url:
        raise SigningError("Key Vault Key no configurada (CR_FE_KV_URL / CR_FE_KV_KEY_ID).")

    # Parse documento (MR ya validado por XSD antes)
    doc = etree.fromstring(xml_bytes)

    # Crear ds:Signature (Id fijo para Target de XAdES)
    sig = etree.Element("{%s}Signature" % DS, nsmap={"ds": DS, "xades": XADES})
    sig.set("Id", "Signature-1")

    # ---- SignedProperties (XAdES-EPES) ----
    qprops = etree.Element("{%s}QualifyingProperties" % XADES)
    qprops.set("Target", "#Signature-1")

    sprops = etree.SubElement(qprops, "{%s}SignedProperties" % XADES)
    sprops.set("Id", "SignedProperties-1")

    ssp = etree.SubElement(sprops, "{%s}SignedSignatureProperties" % XADES)

    # SigningTime
    stime = etree.SubElement(ssp, "{%s}SigningTime" % XADES)
    stime.text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # SigningCertificate (CertDigest + IssuerSerial)
    der = _load_cert_der_from_kv()
    der_b64 = base64.b64encode(der).decode()
    issuer, serial = _x509_fields_from_der(der)
    sc = etree.SubElement(ssp, "{%s}SigningCertificate" % XADES)
    sc_cert = etree.SubElement(sc, "{%s}Cert" % XADES)
    sc_digest = etree.SubElement(sc_cert, "{%s}CertDigest" % XADES)
    dm = etree.SubElement(sc_digest, "{%s}DigestMethod" % DS)
    dm.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")
    dv = etree.SubElement(sc_digest, "{%s}DigestValue" % DS)
    dv.text = base64.b64encode(hashlib.sha256(der).digest()).decode()
    sc_is = etree.SubElement(sc_cert, "{%s}IssuerSerial" % XADES)
    is_name = etree.SubElement(sc_is, "{%s}X509IssuerName" % DS)
    is_name.text = issuer
    is_serial = etree.SubElement(sc_is, "{%s}X509SerialNumber" % DS)
    is_serial.text = str(serial)

    # SignaturePolicyIdentifier (EPES)
    spi = etree.SubElement(ssp, "{%s}SignaturePolicyIdentifier" % XADES)
    spid = etree.SubElement(spi, "{%s}SignaturePolicyId" % XADES)
    spid_id = etree.SubElement(spid, "{%s}SigPolicyId" % XADES)
    spid_ident = etree.SubElement(spid_id, "{%s}Identifier" % XADES)
    spid_ident.text = settings.sign_policy_uri  # <<< define tu política oficial >>>
    spid_hash = etree.SubElement(spid, "{%s}SigPolicyHash" % XADES)
    spid_hash_dm = etree.SubElement(spid_hash, "{%s}DigestMethod" % DS)
    spid_hash_dm.set("Algorithm", settings.sign_policy_hash_alg)
    spid_hash_dv = etree.SubElement(spid_hash, "{%s}DigestValue" % DS)
    spid_hash_dv.text = settings.sign_policy_hash_b64  # <<< digest (Base64) de la política >>>

    # ---- SignedInfo con 2 referencias: documento y SignedProperties ----
    s_info = etree.Element("{%s}SignedInfo" % DS)
    c14n = etree.SubElement(s_info, "{%s}CanonicalizationMethod" % DS)
    c14n.set("Algorithm", "http://www.w3.org/2001/10/xml-exc-c14n#")
    sm = etree.SubElement(s_info, "{%s}SignatureMethod" % DS)
    sm.set("Algorithm", "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")

    # Ref al documento (URI="")
    ref_doc = etree.SubElement(s_info, "{%s}Reference" % DS)
    ref_doc.set("URI", "")
    trans = etree.SubElement(ref_doc, "{%s}Transforms" % DS)
    t1 = etree.SubElement(trans, "{%s}Transform" % DS)
    t1.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    t2 = etree.SubElement(trans, "{%s}Transform" % DS)
    t2.set("Algorithm", "http://www.w3.org/2001/10/xml-exc-c14n#")
    dm1 = etree.SubElement(ref_doc, "{%s}DigestMethod" % DS)
    dm1.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")
    dv1 = etree.SubElement(ref_doc, "{%s}DigestValue" % DS)
    dv1.text = base64.b64encode(hashlib.sha256(_c14n(doc)).digest()).decode()

    # Ref a SignedProperties (Type=SignedProperties)
    ref_sp = etree.SubElement(s_info, "{%s}Reference" % DS)
    ref_sp.set("URI", "#SignedProperties-1")
    ref_sp.set("Type", "http://uri.etsi.org/01903#SignedProperties")
    dm2 = etree.SubElement(ref_sp, "{%s}DigestMethod" % DS)
    dm2.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")
    dv2 = etree.SubElement(ref_sp, "{%s}DigestValue" % DS)
    dv2.text = base64.b64encode(hashlib.sha256(_c14n(sprops)).digest()).decode()

    # ---- SignatureValue (Key Vault) ----
    cred = DefaultAzureCredential()
    crypto = CryptographyClient(key_identifier=settings.kv_key_id, credential=cred)
    si_c14n = _c14n(s_info)
    signed = crypto.sign(SignatureAlgorithm.rs256, si_c14n)
    sig_val = etree.Element("{%s}SignatureValue" % DS)
    sig_val.text = base64.b64encode(signed.signature).decode()

    # ---- KeyInfo con X509Certificate ----
    ki = etree.Element("{%s}KeyInfo" % DS)
    x509data = etree.SubElement(ki, "{%s}X509Data" % DS)
    x509cert = etree.SubElement(x509data, "{%s}X509Certificate" % DS)
    x509cert.text = der_b64

    # ---- Ensamblar ds:Signature ----
    sig.append(s_info)
    sig.append(sig_val)
    sig.append(ki)
    # xades:QualifyingProperties debe ir como hijo de ds:Signature
    sig.append(qprops)

    # Insertar firma (enveloped)
    doc.append(sig)

    return SignResult(
        signed_xml=etree.tostring(doc, encoding="UTF-8", xml_declaration=True),
        signature_method="xades-epes-rsa-sha256",
        key_id=settings.kv_key_id,
    )
