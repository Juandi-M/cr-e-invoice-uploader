locals {
  st_name = lower(substr(replace("${var.project_name}${var.env}st", "-", ""), 0, 24))
}

resource "azurerm_storage_account" "st" {
  name                     = local.st_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  allow_blob_public_access = false
}
