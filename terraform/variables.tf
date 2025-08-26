variable "project_name" {
  type        = string
  description = "Nombre base del proyecto"
  default     = "cr-e-invoice"
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "eastus"
}

variable "env" {
  type        = string
  description = "sandbox | prod"
  default     = "sandbox"
}
