import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # --- Runtime / Env ---
    env: str = os.getenv("CR_FE_ENV", "sandbox").strip().lower()  # sandbox | prod
    tenant_id: str = os.getenv("CR_TENANT_ID", "<<< SET TENANT (cedula) >>>").strip()

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

    # --- IdP (Keycloak ROPC) ---
    idp_username: str = os.getenv("CR_FE_IDP_USERNAME", "<<< SET USERNAME >>>")
    idp_password: str = os.getenv("CR_FE_IDP_PASSWORD", "<<< SET PASSWORD >>>")

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
    kv_url: str = os.getenv("CR_FE_KV_URL", "<<< SET KEY VAULT URL >>>").strip()      # https://xxx.vault.azure.net/
    kv_key_id: str = os.getenv("CR_FE_KV_KEY_ID", "<<< SET KEY ID >>>").strip()       # https://.../keys/name/version
    kv_cert_id: str = os.getenv("CR_FE_KV_CERT_ID", "<<< SET CERT ID >>>").strip()    # https://.../certificates/name/version

    # --- XAdES-EPES Policy (RELLENAR CON TU POLÍTICA OFICIAL) ---
    # URI de la política y su hash SHA-256 en Base64 (digest del documento/identificador de política)
    sign_policy_uri: str = os.getenv("CR_FE_XADES_POLICY_URI", "<<< SET POLICY URI >>>")
    sign_policy_hash_b64: str = os.getenv("CR_FE_XADES_POLICY_HASH_B64", "<<< SET POLICY DIGEST B64 >>>")
    # Algoritmo del digest (normalmente SHA-256)
    sign_policy_hash_alg: str = os.getenv("CR_FE_XADES_POLICY_HASH_ALG", "http://www.w3.org/2001/04/xmlenc#sha256")

    # --- Graph (opcional) ---
    graph_tenant_id: str = os.getenv("GRAPH_TENANT_ID", "")
    graph_client_id: str = os.getenv("GRAPH_CLIENT_ID", "")
    graph_client_secret: str = os.getenv("GRAPH_CLIENT_SECRET", "")
    graph_user_id: str = os.getenv("GRAPH_USER_ID", "")

    # --- App Insights (opcional) ---
    appinsights_connstr: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

settings = Settings()
