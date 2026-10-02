"""YOVA API n8n webhook connector."""

__version__ = "0.1.0"

from .n8n_connector import N8nConnector

__all__ = ["N8nConnector", "__version__"]
