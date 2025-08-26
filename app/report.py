from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
from app.config import settings

if settings.appinsights_connstr:
    try:
        from opencensus.ext.azure.log_exporter import AzureLogHandler
        h = AzureLogHandler(connection_string=settings.appinsights_connstr)
        h.setLevel(logging.INFO)
        logging.getLogger().addHandler(h)
    except Exception:
        pass

logging.getLogger().setLevel(logging.INFO)

@dataclass
class StepEvent:
    step: str
    tenant: str
    message_id: str
    status: str = "ok"
    note: Optional[str] = None
    extras: Optional[Dict[str,Any]] = None

def log_event(evt: StepEvent):
    logging.info("[%s] tenant=%s msg=%s status=%s note=%s extras=%s",
                 evt.step, evt.tenant, evt.message_id, evt.status, evt.note, evt.extras or {})
