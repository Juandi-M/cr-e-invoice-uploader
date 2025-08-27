resource "azurerm_service_plan" "plan" {
  name                = "${var.project_name}-${var.env}-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1" # consumo
}

resource "azurerm_linux_function_app" "func" {
  name                       = "${var.project_name}-${var.env}-func"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  storage_account_name       = azurerm_storage_account.st.name
  storage_account_access_key = azurerm_storage_account.st.primary_access_key
  service_plan_id            = azurerm_service_plan.plan.id

  identity { type = "SystemAssigned" }

  site_config {
    application_stack { python_version = "3.10" }
    use_32_bit_worker = false
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME               = "python"
    AzureWebJobsStorage                    = azurerm_storage_account.st.primary_connection_string
    WEBSITE_RUN_FROM_PACKAGE               = "1"

    APPINSIGHTS_INSTRUMENTATIONKEY         = azurerm_application_insights.appi.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING  = azurerm_application_insights.appi.connection_string

    # Tu app
    CR_FE_ENV         = var.env
    CR_TENANT_ID      = var.cr_tenant_id
    CR_FE_MR_XSD_PATH = var.mr_xsd_path
    CR_FE_INV_XSD_PATH= var.inv_xsd_path

    CR_FE_XADES_POLICY_URI  = var.xades_policy_uri
    CR_FE_XADES_POLICY_HASH_ALG = var.xades_policy_hash_alg
    CR_FE_XADES_POLICY_HASH_B64 = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.xades_policy_hash_b64.id})"

    # Key Vault (IDs completos de key y cert los metés luego; aquí solo el vault URL)
    CR_FE_KV_URL = azurerm_key_vault.kv.vault_uri

    # Graph (delegated Outlook.com) via KV references
    GRAPH_CLIENT_ID     = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.graph_client_id.id})"
    GRAPH_CLIENT_SECRET = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.graph_client_secret.id})"
    GRAPH_REFRESH_TOKEN = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.graph_refresh_token.id})"
    GRAPH_USER_ID       = var.graph_user_id

    # Hacienda IdP creds via KV references
    CR_FE_IDP_USERNAME  = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.idp_username.id})"
    CR_FE_IDP_PASSWORD  = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.idp_password.id})"
  }
}

# RBAC para que la Function pueda firmar y leer KV
resource "azurerm_role_assignment" "kv_crypto" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Crypto User"
  principal_id         = azurerm_linux_function_app.func.identity.principal_id
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_function_app.func.identity.principal_id
}

resource "azurerm_role_assignment" "kv_certs_reader" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Certificates Officer" # o "Key Vault Certificates Reader"
  principal_id         = azurerm_linux_function_app.func.identity.principal_id
}
