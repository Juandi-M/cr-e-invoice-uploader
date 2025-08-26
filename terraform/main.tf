resource "azurerm_resource_group" "rg" {
  name     = "${var.project_name}-${var.env}-rg"
  location = var.location
}

resource "azurerm_storage_account" "st" {
  name                     = replace("${var.project_name}${var.env}st", "-", "")
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_application_insights" "appi" {
  name                = "${var.project_name}-${var.env}-appi"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}

resource "azurerm_key_vault" "kv" {
  name                        = "${var.project_name}-${var.env}-kv"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = false
  soft_delete_retention_days  = 7
}

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

  site_config {
    application_stack {
      python_version = "3.10"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME             = "python"
    AzureWebJobsStorage                  = azurerm_storage_account.st.primary_connection_string
    APPINSIGHTS_INSTRUMENTATIONKEY       = azurerm_application_insights.appi.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.appi.connection_string

    # Ejemplos (ajustar según tu local.settings.json)
    CR_FE_ENV       = var.env
    CR_TENANT_ID    = "3101509572"
    CR_FE_MR_XSD_PATH = "./xsd/MensajeReceptor_V4.4.xsd"
    CR_FE_INV_XSD_PATH = "./xsd/FacturaElectronica_V4.4.xsd"
  }
}
