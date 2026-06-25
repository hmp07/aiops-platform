"""DataSource Registry — maps source_type to adapter class."""
from app.integrations.base import BaseAdapter

_registry: dict[str, type[BaseAdapter]] = {}

def register(source_type: str, adapter_cls: type[BaseAdapter]):
    _registry[source_type] = adapter_cls

def get_adapter(source_type: str) -> type[BaseAdapter] | None:
    return _registry.get(source_type)

def list_types() -> list[dict]:
    return [
        {"type": "zabbix", "name": "Zabbix", "description": "Infrastructure monitoring — alerts, metrics, hosts", "default_port": 80},
        {"type": "prometheus", "name": "Prometheus", "description": "Metrics and time-series monitoring", "default_port": 9090},
        {"type": "itop", "name": "iTop CMDB", "description": "Configuration Management Database — asset sync", "default_port": 80},
        {"type": "signoz", "name": "SigNoz", "description": "Application performance monitoring — traces, metrics, logs", "default_port": 3301},
    ]
