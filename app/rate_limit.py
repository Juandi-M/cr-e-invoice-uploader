# app/rate_limit.py
from __future__ import annotations
import time
from typing import Optional

def sleep_from_headers(headers: dict, default_interval: int = 5) -> int:
    """
    Usa X-RateLimit-Remaining/Reset si vienen; devuelve segundos dormidos.
    """
    remaining = headers.get("X-Ratelimit-Remaining") or headers.get("X-RateLimit-Remaining")
    reset = headers.get("X-Ratelimit-Reset") or headers.get("X-RateLimit-Reset")
    if remaining is not None and str(remaining).isdigit() and int(remaining) == 0:
        try:
            s = int(reset)
            time.sleep(max(s, default_interval))
            return max(s, default_interval)
        except Exception:
            pass
    time.sleep(default_interval)
    return default_interval
