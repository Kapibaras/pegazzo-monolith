"""Document type taxonomy registry.

Loads JSON definitions from ``app/documents/doc_types/`` at import time and
exposes helpers consumed by schemas, services and the extraction pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.enum.document import DocumentType

DOC_TYPES_DIR = Path(__file__).resolve().parent / "doc_types"

_REGISTRY: dict[str, dict[str, Any]] = {}


def _load_registry() -> None:
    for path in sorted(DOC_TYPES_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            spec = json.load(f)

        name = spec["name"]
        if name not in {member.value for member in DocumentType}:
            msg = f"{path.name}: name '{name}' is not a valid DocumentType member"
            raise ValueError(msg)

        _REGISTRY[name] = spec


_load_registry()


def get_doc_type_spec(doc_type: str) -> dict[str, Any] | None:
    """Return the full spec dict for *doc_type*, or ``None`` if unknown."""
    return _REGISTRY.get(doc_type)


def is_valid_for_entity(doc_type: str, entity_type: str) -> bool:
    """Return ``True`` when *doc_type* is allowed on *entity_type*."""
    spec = _REGISTRY.get(doc_type)
    if spec is None:
        return False
    return entity_type in spec.get("allowed_entity_types", [])


def get_analyzable_types() -> list[str]:
    """Return a list of document type names that can be analyzed by AI."""
    return [name for name, spec in _REGISTRY.items() if spec.get("ai_analyzable")]


def get_all_specs() -> dict[str, dict[str, Any]]:
    """Return the full registry (read-only view)."""
    return dict(_REGISTRY)
