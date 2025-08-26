import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # --- Runtime / Env ---
    env: str = os.getenv("CR_FE_ENV", "sandbox").strip().lower()  # sandbox | prod
    tenant_id: str = os.getenv("CR_TENANT_ID", "3101509572").strip()  # SIN guiones

    # --- Storage (Azure) ---
    storage_conn: str = os.getenv("AzureWebJobsStorage", "UseDevelopmentStorage=true")
    blob_raw: str = os.getenv("BLOB_CONTAINER_RAW", "raw")
    blob_mr: str = os.getenv("BLOB_CONTAINER_MR", "mr")
    blob_signed: str = os.getenv("BLOB_CONTAINER_SIGNED", "signed")
    blob_resp: str = os.getenv("BLOB_CONTAINER_RESPONSES", "responses")
    blob_quar: str = os.getenv("BLOB_CONTAINER_QUAR", "quarantine")

    # --- Queues ---
    q_incoming: str = os.getenv("QUEUE_INCOMING", "q-incoming")
    q_validate: str = os.getenv("QUEUE_VALIDATE", "q-validate")
    q_sign: str = os.getenv("QUEUE_SIGN", "q-sign")
    q_poll: str = os.getenv("QUEUE_POLL", "q-poll")

    # --- XSD (local paths v4.4) ---
    mr_xsd_path: str = os.getenv("CR_FE_MR_XSD_PATH", "./xsd/MensajeReceptor_V4.4.xsd")
    inv_xsd_path: str = os.getenv("CR_FE_INV_XSD_PATH", "./xsd/FacturaElectronica_V4.4.xsd")

    # --- IdP (Hacienda / Keycloak, ROPC) ---
    idp_username: str = os.getenv("CR_FE_IDP_USERNAME", "")  # <- PONER credenciales sandbox/prod
    idp_password: str = os.getenv("CR_FE_IDP_PASSWORD", "")

    @property
    def idp_client_id(self) -> str:
        return "api-stag" if self.env == "sandbox" else "api-prod"

    @property
    def idp_token_url(self) -> str:
        realm = "rut-stag" if self.env == "sandbox" else "rut"
        return f"https://idp.comprobanteselectronicos.go.cr/auth/realms/{realm}/protocol/openid-connect/token"

    # --- API Recepción ---
    @property
    def recepcion_base_url(self) -> str:
        base = "recepcion-sandbox" if self.env == "sandbox" else "recepcion"
        return f"https://api.comprobanteselectronicos.go.cr/{base}/v1"

    # --- Firma (Key Vault) ---
    kv_url: str = os.getenv("CR_FE_KV_URL", "").strip()      # https://<tu-vault>.vault.azure.net/
    kv_key_id: str = os.getenv("CR_FE_KV_KEY_ID", "").strip()   # https://.../keys/<name>/<version>
    kv_cert_id: str = os.getenv("CR_FE_KV_CERT_ID", "").strip() # https://.../certificates/<name>/<version>

    # --- XAdES-EPES Policy (v4.4 oficial) ---
    # URI oficial del PDF de la resolución técnica (Anexos/Estructuras v4.4)
    # Fuente: documentación v4.4 de Hacienda (Anexos y API). 
    # https://cdn.comprobanteselectronicos.go.cr/xml-schemas/Resolución...pdf  (ver cita)
    sign_policy_uri: str = os.getenv("CR_FE_XADES_POLICY_URI",
        "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/Resoluci%C3%B3n_General_sobre_disposiciones_t%C3%A9cnicas_comprobantes_electr%C3%B3nicos_para_efectos_tributarios.pdf"
    )

    # Algoritmo del digest (SHA-256)
    sign_policy_hash_alg: str = os.getenv(
        "CR_FE_XADES_POLICY_HASH_ALG",
        "http://www.w3.org/2001/04/xmlenc#sha256"
    )

    # Digest de la política en Base64 (mejor desde env; default de demo)
    sign_policy_hash_b64: str = os.getenv(
        "CR_FE_XADES_POLICY_HASH_B64",
        "REPLACE_WITH_BASE64_SHA256_OF_POLICY_PDF"
    )
    
    # --- Graph (obligatorio en tu flujo) ---
    graph_tenant_id: str = os.getenv("GRAPH_TENANT_ID", "")
    graph_client_id: str = os.getenv("GRAPH_CLIENT_ID", "")
    graph_client_secret: str = os.getenv("GRAPH_CLIENT_SECRET", "")
    graph_user_id: str = os.getenv("GRAPH_USER_ID", "")

    # --- App Insights (opcional) ---
    appinsights_connstr: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

settings = Settings()
