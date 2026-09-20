"""Corpus ingestion: download, verify, and extract flow records.

The exporter here is applied identically to every corpus. That is the whole
point of the module -- see exporter.py and plan section A3.
"""

from oran_ids.ingest.exporter import (
    EXPORTER_VERSION,
    FEATURE_COLUMNS,
    ExporterConfig,
    export_file,
)

__all__ = ["EXPORTER_VERSION", "FEATURE_COLUMNS", "ExporterConfig", "export_file"]
