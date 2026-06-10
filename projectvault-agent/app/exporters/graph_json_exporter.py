"""Export graph.json for visualization and downstream tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.graph.state import ProjectVaultState


class GraphJsonExporter:
    def build_payload(self, state: ProjectVaultState) -> dict[str, list[dict[str, Any]]]:
        return {
            "nodes": [self._normalize_node(node) for node in state["graph_nodes"]],
            "edges": [self._normalize_edge(edge) for edge in state["graph_edges"]],
        }

    def export(self, state: ProjectVaultState) -> dict[str, Any]:
        payload = self.build_payload(state)
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        planned_file = {"path": "graph.json", "content": content, "payload": payload}

        if state["mode"] == "write":
            output_dir = Path(state["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "graph.json").write_text(content, encoding="utf-8")

        return planned_file

    def _normalize_node(self, node: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "id": str(node.get("id", "")),
            "label": str(node.get("label", "")),
            "type": str(node.get("type", "")),
        }
        if node.get("type_label"):
            payload["type_label"] = str(node["type_label"])
        properties = node.get("properties")
        if isinstance(properties, dict) and properties:
            payload["properties"] = properties
        return payload

    def _normalize_edge(self, edge: dict[str, Any]) -> dict[str, Any]:
        relation = edge.get("relation", edge.get("type", ""))
        payload = {
            "source": str(edge.get("source", "")),
            "target": str(edge.get("target", "")),
            "relation": str(relation),
        }
        properties = edge.get("properties")
        if isinstance(properties, dict) and properties:
            payload["properties"] = properties
        return payload
