# app/config_loader.py
import json, os
from pathlib import Path

def load_local_settings(path: str = "local.settings.json") -> None:
    """
    Lee local.settings.json y exporta sus 'Values' al entorno (si no existen).
    Prioridad: ENV > JSON. Úsalo solo en local.
    """
    p = Path(path)
    if not p.exists():
        return
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        values = data.get("Values", {}) or {}
        for k, v in values.items():
            # No sobrescribir si ya viene del entorno
            if k not in os.environ and v is not None:
                os.environ[k] = str(v)
    except Exception as e:
        # No rompas el arranque por esto; loguealo si quieres
        print(f"[config_loader] No se pudo cargar {path}: {e}")
