output "function_app_name"      { value = azurerm_linux_function_app.func.name }
output "function_app_hostname"  { value = azurerm_linux_function_app.func.default_hostname }
output "resource_group"         { value = azurerm_resource_group.rg.name }
output "key_vault_name"         { value = azurerm_key_vault.kv.name }
output "storage_account_name"   { value = azurerm_storage_account.st.name }
output "app_insights_name"      { value = azurerm_application_insights.appi.name }
