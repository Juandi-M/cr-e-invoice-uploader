resource "azurerm_key_vault" "kv" {
  name                        = "${var.project_name}-${var.env}-kv"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = false
  soft_delete_retention_days  = 7
  enable_rbac_authorization   = true  # Usaremos RBAC, no access policies clásicas
}

# Secrets iniciales (opcionales). Podés dejarlos vacíos y luego rotarlos.
resource "azurerm_key_vault_secret" "graph_client_id" {
  name         = "GRAPH-CLIENT-ID"
  value        = var.graph_client_id
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "graph_client_secret" {
  name         = "GRAPH-CLIENT-SECRET"
  value        = var.graph_client_secret
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "graph_refresh_token" {
  name         = "GRAPH-REFRESH-TOKEN"
  value        = var.graph_refresh_token
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "idp_username" {
  name         = "HACIENDa-IDP-USERNAME"
  value        = var.idp_username
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "idp_password" {
  name         = "HACIENDa-IDP-PASSWORD"
  value        = var.idp_password
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "xades_policy_hash_b64" {
  name         = "XADES-POLICY-HASH-B64"
  value        = var.xades_policy_hash_b64
  key_vault_id = azurerm_key_vault.kv.id
}
