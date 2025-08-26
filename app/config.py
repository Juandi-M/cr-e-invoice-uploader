import os
from dataclasses import dataclass

_PLACEHOLDER = "<<< SET THIS >>>"

@dataclass(frozen=True)
class Settings:
    # -------- Runtime / Env --------
    env: str = os.getenv("CR_FE_ENV", "sandbox").strip().lower()  # sandbox|prod

    # -------- Storage (Functions) --------
    storage_conn: str = os.getenv("AzureWebJobsStorage", "UseDevelopmentStorage=true")
    blob_raw: str = os.getenv("BLOB_CONTAINER_RAW", "raw")
    blob_valid: str = os.getenv("BLOB_CONTAINER_VALID", "valid")
    blob_out: str = os.getenv("BLOB_CONTAINER_OUT", "out")
    blob_quar: str = os.getenv("BLOB_CONTAINER_QUAR", "quarantine")

    # -------- Queues --------
    q_incoming: str = os.getenv("QUEUE_INCOMING", "q-incoming")
    q_validate: str = os.getenv("QUEUE_VALIDATE", "q-validate")
    q_sign: str = os.getenv("QUEUE_SIGN", "q-sign")

    # -------- Hacienda IdP (Keycloak ROPC) --------
    idp_username: str = os.getenv("CR_FE_IDP_USERNAME", _PLACEHOLDER)  # ej: cpf-01-XXXX-XXXX@stag.comprobanteselectronicos.go.cr
    idp_password: str = os.getenv("CR_FE_IDP_PASSWORD", _PLACEHOLDER)
    # client_id cambia según entorno (api-stag | api-prod)
    @property
    def idp_client_id(self) -> str:
        return "api-stag" if self.env == "sandbox" else "api-prod"

    @property
    def idp_token_url(self) -> str:
        realm = "rut-stag" if self.env == "sandbox" else "rut"
        return f"https://idp.comprobanteselectronicos.go.cr/auth/realms/{realm}/protocol/openid-connect/token"

    # -------- Hacienda API Recepción --------
    @property
    def recepcion_base_url(self) -> str:
        base = "recepcion-sandbox" if self.env == "sandbox" else "recepcion"
        return f"https://api.comprobanteselectronicos.go.cr/{base}/v1"

    # -------- MR / XSD (opcional) --------
    mr_xsd_path: str = os.getenv("CR_FE_MR_XSD_PATH", "")  # ej: ./xsd/v4.4/mensajeReceptor.xsd
    inv_xsd_path: str = os.getenv("CR_FE_INV_XSD_PATH", "")  # ej: ./xsd/v4.4/facturaElectronica.xsd

    # -------- Firma --------
    sign_backend: str = os.getenv("CR_FE_SIGN_BACKEND", "PEM")  # PEM | KEYVAULT
    pem_cert_path: str = os.getenv("CR_FE_PEM_CERT_PATH", _PLACEHOLDER)  # ej: ./certs/cert.pem
    pem_key_path: str = os.getenv("CR_FE_PEM_KEY_PATH", _PLACEHOLDER)    # ej: ./certs/key.pem (PKCS#8)
    pem_key_password: str = os.getenv("CR_FE_PEM_KEY_PASSWORD", "")      # si aplica

    # Key Vault (si usas KEYVAULT) — hook listo
    keyvault_url: str = os.getenv("CR_FE_KV_URL", "")                     # ej: https://mi-kv.vault.azure.net/
    keyvault_key_id: str = os.getenv("CR_FE_KV_KEY_ID", "")               # ej: https://.../keys/mi-key/xxxxxxxx

    # -------- MS Graph (adjuntos) --------
    graph_tenant_id: str = os.getenv("GRAPH_TENANT_ID", _PLACEHOLDER)
    graph_client_id: str = os.getenv("GRAPH_CLIENT_ID", _PLACEHOLDER)
    graph_client_secret: str = os.getenv("GRAPH_CLIENT_SECRET", _PLACEHOLDER)
    graph_user_id: str = os.getenv("GRAPH_USER_ID", _PLACEHOLDER)  # buzón origen: UPN o GUID

    # -------- App Insights (opcional) --------
    appinsights_connstr: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

settings = Settings()
