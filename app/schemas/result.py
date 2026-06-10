"""Pipeline result schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.schemas.graph_item import KnowledgeGraph


@dataclass
class ProjectVaultResult:
    graph: KnowledgeGraph
    exported_paths: list[Path] = field(default_factory=list)

