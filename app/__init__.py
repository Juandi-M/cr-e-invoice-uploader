# app/__init__.py
import os

# Cargar settings locales si estamos en dev (no en Azure)
if os.getenv("WEBSITE_SITE_NAME") is None:
    try:
        from app.config_loader import load_local_settings
        load_local_settings()  # intenta leer local.settings.json
    except Exception as e:
        print(f"[init] Aviso: no se cargaron local settings: {e}")

__version__ = "1.0.0"
