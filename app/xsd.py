from lxml import etree
from functools import lru_cache
from pathlib import Path

def _schema_from(path: str) -> etree.XMLSchema:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"XSD not found: {p}")
    with p.open("rb") as f:
        doc = etree.parse(f)
    return etree.XMLSchema(doc)

@lru_cache(maxsize=1)
def invoice_schema(path: str) -> etree.XMLSchema:
    return _schema_from(path)

@lru_cache(maxsize=1)
def mr_schema(path: str) -> etree.XMLSchema:
    return _schema_from(path)

def validate_xml(xml_bytes: bytes, schema: etree.XMLSchema) -> None:
    schema.assertValid(etree.fromstring(xml_bytes))
