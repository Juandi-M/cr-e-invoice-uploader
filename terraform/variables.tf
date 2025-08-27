variable "project_name" { type = string  default = "cr-e-invoice" }
variable "env"          { type = string  default = "sandbox" } # sandbox | prod
variable "location"     { type = string  default = "eastus" }

# Cédula del receptor (sin guiones)
variable "cr_tenant_id" { type = string  default = "3101509572" }

# XSD paths en runtime dentro del zip (tú los tienes en /xsd)
variable "mr_xsd_path"  { type = string  default = "./xsd/MensajeReceptor_V4.4.xsd" }
variable "inv_xsd_path" { type = string  default = "./xsd/FacturaElectronica_V4.4.xsd" }

# Política XAdES (URI y hash Base64)
variable "xades_policy_uri"      { type = string  default = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/Resoluci%C3%B3n_General_sobre_disposiciones_t%C3%A9cnicas_comprobantes_electr%C3%B3nicos_para_efectos_tributarios.pdf" }
variable "xades_policy_hash_alg" { type = string  default = "http://www.w3.org/2001/04/xmlenc#sha256" }
variable "xades_policy_hash_b64" { type = string  default = "REPLACE_WITH_BASE64_SHA256_OF_POLICY_PDF" }

# Secrets iniciales (pueden quedar vacíos y luego los updates por portal/KV)
variable "graph_client_id"     { type = string  default = "" }
variable "graph_client_secret" { type = string  default = "" }
variable "graph_refresh_token" { type = string  default = "" }
variable "graph_user_id"       { type = string  default = "cromofac@outlook.com" }

variable "idp_username"        { type = string  default = "" }
variable "idp_password"        { type = string  default = "" }
