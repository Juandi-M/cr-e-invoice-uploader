# cr-e-invoice-uploader

## 📌 Descripción

`cr-e-invoice-uploader` es un sistema **serverless** para la **recepción, almacenamiento, procesamiento y generación de respuestas de facturas electrónicas XML**.
Automatiza la integración con correos electrónicos, garantizando seguridad, idempotencia y costos prácticamente nulos en Azure.

---

## 🎯 Objetivos

* Extraer facturas electrónicas desde correos con **Microsoft Graph API**.
* Guardar XML en **Azure Blob Storage** de manera estructurada y segura.
* Procesar facturas con **Azure Functions** para generar el XML de respuesta.
* Garantizar **idempotencia** mediante identificadores únicos.
* Proteger secretos y llaves con **Azure Key Vault**.

---

## 🏗️ Arquitectura

El sistema sigue un enfoque **event-driven** basado en servicios de Azure:

1. **Microsoft Graph API** → Obtención de facturas XML desde la bandeja de entrada.
2. **Azure Functions (Python)** → Orquestación de flujo y procesamiento de documentos.
3. **Azure Blob Storage** → Almacenamiento seguro y económico de XML.
4. **Azure Key Vault** → Manejo de credenciales y llaves criptográficas.
5. **Azure Queue Storage** → Coordinación opcional de eventos y cargas.
6. **Application Insights** *(opcional)* → Monitoreo y trazabilidad.

---

## 🚀 Flujo de procesamiento

1. Una factura XML llega por correo.
2. Microsoft Graph API descarga el adjunto.
3. Azure Function procesa el archivo:

   * Valida estructura
   * Aplica idempotencia
   * Genera XML de respuesta
4. Se almacena en Azure Blob Storage.
5. Opcional: se envía respuesta o se dispara un evento en Azure Queue.

---

## 🛠️ Tecnologías utilizadas

* **Lenguaje:** Python
* **Azure Functions**
* **Azure Blob Storage**
* **Azure Key Vault**
* **Microsoft Graph API**
* **Azure Queue Storage** (opcional)
* **Application Insights** (opcional)

---

## 🔐 Seguridad

* Credenciales y llaves almacenadas en **Azure Key Vault**.
* Acceso controlado mediante **Managed Identities**.
* Autenticación OAuth2 para Microsoft Graph API.

---

## 💰 Costos estimados

El diseño es **costo cero** en uso bajo.

* Azure Functions → <\$1/mes
* Azure Storage → <\$1/mes
* Azure Queue → <\$1/mes
* Application Insights → \~\$2–5/mes (solo si se activa)

👉 **Costo total:** **0 USD** (sin monitoreo adicional).

---

## ⚙️ Despliegue

### 1. Requisitos previos

* Azure CLI instalado
* Subscripción activa en Azure
* Python 3.9+
* Permisos para usar Microsoft Graph API

### 2. Variables de entorno requeridas

```bash
GRAPH_CLIENT_ID=<client-id>
GRAPH_TENANT_ID=<tenant-id>
GRAPH_CLIENT_SECRET=<secret>
AZURE_STORAGE_CONNECTION=<storage-conn>
AZURE_KEY_VAULT_URI=<vault-uri>
```

### 3. Despliegue en Azure

```bash
# Crear Function App
az functionapp create \
  --resource-group myResourceGroup \
  --consumption-plan-location eastus \
  --runtime python \
  --functions-version 4 \
  --name cr-e-invoice-uploader \
  --storage-account mystorageaccount

# Publicar funciones
func azure functionapp publish cr-e-invoice-uploader
```

---

## 📊 Monitoreo

* Logs nativos de Azure Functions
* Integración opcional con **Application Insights** para trazabilidad avanzada


¿Querés que además te arme un **diagrama visual en Markdown/mermaid** con el flujo de componentes para incluirlo en el README?
