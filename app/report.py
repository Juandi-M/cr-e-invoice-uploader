"""
Telemetry y logging. Usa App Insights si hay CONNECTION STRING, sino logging.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging, os
from app.config import settings

_USE_AI = bool(settings.appinsights_connstr)

if _USE_AI:
    # opencensus-ext-azure v1.x
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    _handler = AzureLogHandler(connection_string=settings.appinsights_connstr)
    _handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(_handler)

logging.getLogger().setLevel(logging.INFO)

@dataclass
class StepEvent:
    step: str
    tenant: str
    message_id: str
    extras: Optional[Dict[str, Any]] = None
    status: str = "ok"
    note: Optional[str] = None

def log_event(evt: StepEvent):
    logging.info(
        "[%s] tenant=%s msg=%s status=%s note=%s extras=%s",
        evt.step, evt.tenant, evt.message_id, evt.status, evt.note, evt.extras or {}
    )
