"""Build ProjectVault graph.json nodes and edges."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.knowledge.schema import EdgeType, NodeType, make_edge, make_node, node_id, slugify


class ProjectGraphBuilder:
    """Create a lightweight graph from scanned files and Gemini analyses."""

    project_node_id = "project:local"

    def build(
        self,
        files: list[dict[str, Any]],
        analyzed_files: list[dict[str, Any]],
        input_dir: str,
    ) -> dict[str, list[dict[str, Any]]]:
        nodes_by_id: dict[str, dict[str, Any]] = {}
        edge_keys: set[tuple[str, str, str]] = set()
        edges: list[dict[str, Any]] = []

        project_label = Path(input_dir).name or "로컬 프로젝트"
        self._add_node(
            nodes_by_id,
            make_node(self.project_node_id, project_label, NodeType.PROJECT, {"input_dir": input_dir}),
        )

        file_ids_by_path: dict[str, str] = {}
        for file_item in files:
            relative_path = relative_file_path(file_item, input_dir)
            file_id = node_id(NodeType.FILE, relative_path)
            file_ids_by_path[relative_path] = file_id
            self._add_node(
                nodes_by_id,
                make_node(
                    file_id,
                    relative_path,
                    NodeType.FILE,
                    {
                        "path": str(file_item.get("path", "")),
                        "filename": str(file_item.get("filename", Path(relative_path).name)),
                        "extension": str(file_item.get("extension", "")),
                        "file_type": str(file_item.get("file_type", "document")),
                        "content_preview": str(file_item.get("content_preview", "")),
                    },
                ),
            )
            self._add_edge(edges, edge_keys, make_edge(self.project_node_id, file_id, EdgeType.CONTAINS))

        for analysis in analyzed_files:
            relative_path = relative_file_path({"path": analysis.get("file_path", "")}, input_dir)
            file_id = file_ids_by_path.get(relative_path, node_id(NodeType.FILE, relative_path))
            if relative_path not in file_ids_by_path:
                file_ids_by_path[relative_path] = file_id
                self._add_node(
                    nodes_by_id,
                    make_node(
                        file_id,
                        relative_path,
                        NodeType.FILE,
                        {
                            "path": str(analysis.get("file_path", "")),
                            "filename": Path(relative_path).name,
                            "extension": Path(relative_path).suffix,
                            "file_type": str(analysis.get("file_type", "document")),
                            "content_preview": "",
                            "source": str(analysis.get("source", "")),
                        },
                    ),
                )
                self._add_edge(edges, edge_keys, make_edge(self.project_node_id, file_id, EdgeType.CONTAINS))

            requirement_ids = self._add_items(
                nodes_by_id=nodes_by_id,
                edges=edges,
                edge_keys=edge_keys,
                file_id=file_id,
                items=analysis.get("requirements", []),
                node_type=NodeType.REQUIREMENT,
                label_key="title",
                file_relation=EdgeType.REQUIRES,
            )
            self._add_items(
                nodes_by_id=nodes_by_id,
                edges=edges,
                edge_keys=edge_keys,
                file_id=file_id,
                items=analysis.get("concepts", []),
                node_type=NodeType.CONCEPT,
                label_key="name",
                file_relation=EdgeType.MENTIONS,
            )
            task_ids = self._add_items(
                nodes_by_id=nodes_by_id,
                edges=edges,
                edge_keys=edge_keys,
                file_id=file_id,
                items=analysis.get("tasks", []),
                node_type=NodeType.TASK,
                label_key="title",
                file_relation=EdgeType.REQUIRES if analysis.get("file_type") == "assignment_notice" else EdgeType.SUPPORTS,
            )
            self._add_items(
                nodes_by_id=nodes_by_id,
                edges=edges,
                edge_keys=edge_keys,
                file_id=file_id,
                items=analysis.get("errors", []),
                node_type=NodeType.ERROR,
                label_key="title",
                file_relation=EdgeType.OCCURS_IN,
                reverse_file_edge=True,
            )
            self._add_items(
                nodes_by_id=nodes_by_id,
                edges=edges,
                edge_keys=edge_keys,
                file_id=file_id,
                items=analysis.get("decisions", []),
                node_type=NodeType.DECISION,
                label_key="title",
                file_relation=EdgeType.AFFECTS,
                reverse_file_edge=True,
            )

            for task_id in task_ids:
                for requirement_id in requirement_ids:
                    self._add_edge(edges, edge_keys, make_edge(task_id, requirement_id, EdgeType.DEPENDS_ON))

        return {"nodes": list(nodes_by_id.values()), "edges": edges}

    def _add_items(
        self,
        nodes_by_id: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        edge_keys: set[tuple[str, str, str]],
        file_id: str,
        items: object,
        node_type: NodeType,
        label_key: str,
        file_relation: EdgeType,
        reverse_file_edge: bool = False,
    ) -> list[str]:
        added_ids: list[str] = []
        for item in list_of_dicts(items):
            label = str(item.get(label_key, "")).strip()
            if not label:
                continue

            item_node_id = node_id(node_type, label)
            self._add_node(
                nodes_by_id,
                make_node(
                    item_node_id,
                    label,
                    node_type,
                    {**item, "slug": slugify(label)},
                ),
            )
            if reverse_file_edge:
                self._add_edge(edges, edge_keys, make_edge(item_node_id, file_id, file_relation))
            else:
                self._add_edge(edges, edge_keys, make_edge(file_id, item_node_id, file_relation))
            added_ids.append(item_node_id)
        return added_ids

    def _add_node(self, nodes_by_id: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
        existing = nodes_by_id.get(node["id"])
        if existing is None:
            nodes_by_id[node["id"]] = node
            return

        existing_properties = existing.setdefault("properties", {})
        for key, value in node.get("properties", {}).items():
            if key not in existing_properties or not existing_properties[key]:
                existing_properties[key] = value

    def _add_edge(
        self,
        edges: list[dict[str, Any]],
        edge_keys: set[tuple[str, str, str]],
        edge: dict[str, Any],
    ) -> None:
        key = (str(edge["source"]), str(edge["target"]), str(edge["relation"]))
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append(edge)


def list_of_dicts(items: object) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def relative_file_path(file_item: dict[str, Any], input_dir: str) -> str:
    path_value = str(file_item.get("path", "") or file_item.get("file_path", "") or file_item.get("filename", ""))
    if not path_value:
        return "unknown"

    path = Path(path_value)
    try:
        return path.resolve().relative_to(Path(input_dir).resolve()).as_posix()
    except ValueError:
        return path.as_posix()
