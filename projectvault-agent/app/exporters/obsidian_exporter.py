"""Export Obsidian Markdown notes from the project graph."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.graph.state import ProjectVaultState
from app.knowledge.schema import EdgeType, NODE_TYPE_LABELS, NodeType, safe_filename


class ObsidianExporter:
    def export(self, state: ProjectVaultState) -> list[dict[str, Any]]:
        planned_files = self.build_files(state)

        if state["mode"] == "write":
            output_dir = Path(state["output_dir"])
            clean_generated_outputs(output_dir)
            for file_item in planned_files:
                path = output_dir / str(file_item["path"])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(str(file_item["content"]), encoding="utf-8")

        return planned_files

    def build_files(self, state: ProjectVaultState) -> list[dict[str, Any]]:
        context = GraphNoteContext(state)
        files = [
            self._project_index(state, context),
            self._assignment_checklist(state, context),
            self._lecture_concepts(state, context),
            self._code_summary(state, context),
            self._error_log(state, context),
            self._next_actions(state, context),
            self._codex_context_pack(state, context),
            self._obsidian_graph_config(),
            self.build_graph_report(state),
        ]

        for node in state["graph_nodes"]:
            node_type = node.get("type")
            if node_type == NodeType.FILE.value:
                files.append(self._file_note(state, context, node))
            elif node_type == NodeType.CONCEPT.value:
                files.append(self._concept_note(context, node))
            elif node_type == NodeType.TASK.value:
                files.append(self._task_note(context, node))
            elif node_type == NodeType.ERROR.value:
                files.append(self._error_note(context, node))
            elif node_type == NodeType.DECISION.value:
                files.append(self._decision_note(context, node))
            elif node_type == NodeType.REQUIREMENT.value:
                files.append(self._requirement_note(context, node))

        return files

    def _obsidian_graph_config(self) -> dict[str, Any]:
        payload = {
            "collapse-filter": False,
            "search": "",
            "showTags": False,
            "showAttachments": False,
            "hideUnresolved": True,
            "showOrphans": False,
            "collapse-color-groups": False,
            "colorGroups": [
                {"query": "path:Tasks", "color": {"a": 1, "rgb": 16753664}},
                {"query": "path:Requirements", "color": {"a": 1, "rgb": 15337728}},
                {"query": "path:Concepts", "color": {"a": 1, "rgb": 3447003}},
                {"query": "path:Files", "color": {"a": 1, "rgb": 8947848}},
                {"query": "path:Errors", "color": {"a": 1, "rgb": 14237952}},
                {"query": "path:Decisions", "color": {"a": 1, "rgb": 10181046}},
                {"query": "path:00_Project_Index OR path:01_Assignment_Checklist OR path:05_Next_Actions", "color": {"a": 1, "rgb": 2263842}},
            ],
            "collapse-display": False,
            "showArrow": True,
            "textFadeMultiplier": 0,
            "nodeSizeMultiplier": 1.15,
            "lineSizeMultiplier": 1.15,
            "collapse-forces": False,
            "centerStrength": 0.45,
            "repelStrength": 12,
            "linkStrength": 1,
            "linkDistance": 180,
            "scale": 1,
            "close": True,
        }
        return {
            "path": ".obsidian/graph.json",
            "content": json.dumps(payload, ensure_ascii=False, indent=2),
            "kind": "json",
        }

    def build_graph_report(self, state: ProjectVaultState) -> dict[str, Any]:
        node_counts = Counter(str(node.get("type", "")) for node in state["graph_nodes"])
        edge_counts = Counter(str(edge.get("relation", edge.get("type", ""))) for edge in state["graph_edges"])
        security_findings = state.get("security_findings", [])
        security_errors = [
            node
            for node in state["graph_nodes"]
            if node.get("type") == NodeType.ERROR.value and node.get("properties", {}).get("source") == "secret_scanner"
        ]
        security_tasks = [
            node
            for node in state["graph_nodes"]
            if node.get("type") == NodeType.TASK.value and node.get("properties", {}).get("source") == "secret_scanner"
        ]
        lines = [
            *frontmatter("GraphReport", tags=["projectvault", "graph"]),
            "# 그래프 리포트",
            "",
            "## 노드 개수",
            "",
            *[f"- {type_label(node_type)}: {count}" for node_type, count in sorted(node_counts.items())],
            "",
            "## 엣지 개수",
            "",
            *[f"- {relation}: {count}" for relation, count in sorted(edge_counts.items())],
            "",
            "## 보안 점검",
            "",
            f"- 발견 항목: {len(security_findings)}",
            f"- 보안 오류 노드: {len(security_errors)}",
            f"- 보안 할 일 노드: {len(security_tasks)}",
            "- Secret 값: [REDACTED]로 마스킹",
            "",
            "## Google Sheets",
            "",
            f"- Status: {state.get('sheets_result', {}).get('status', 'not-run')}",
            f"- Message: {state.get('sheets_result', {}).get('message', '')}",
            f"- 준비된 row 수: {max(len(state.get('sheets_rows', [])) - 1, 0)}",
            "",
            "## 파일",
            "",
            "- [[graph|graph.json]]",
            "- [[00_Project_Index|프로젝트 인덱스]]",
            "",
        ]
        return {"path": "GRAPH_REPORT.md", "content": "\n".join(lines), "kind": "markdown"}

    def _project_index(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        lines = [
            *frontmatter("Project", tags=["projectvault", "index"]),
            "# 프로젝트 인덱스",
            "",
            "## 작업공간",
            "",
            f"- 입력 폴더: `{state['input_dir']}`",
            f"- 출력 폴더: `{state['output_dir']}`",
            f"- 실행 모드: `{state['mode']}`",
            "",
            "## 바로가기",
            "",
            "- [[01_Assignment_Checklist|과제 체크리스트]]",
            "- [[02_Lecture_Concepts|강의 개념]]",
            "- [[03_Code_Summary|코드 요약]]",
            "- [[04_Error_Log|오류 로그]]",
            "- [[05_Next_Actions|다음 할 일]]",
            "- [[06_Codex_Context_Pack|Codex 컨텍스트 팩]]",
            "- [[GRAPH_REPORT|그래프 리포트]]",
            "",
            "## 파일",
            "",
            *[f"- {context.link(node)}" for node in context.nodes_by_type(NodeType.FILE.value)],
            "",
            "## 할 일",
            "",
            *[f"- [ ] {context.link(node)}" for node in context.nodes_by_type(NodeType.TASK.value)],
            "",
            "## 요구사항",
            "",
            *[f"- {context.link(node)}" for node in context.nodes_by_type(NodeType.REQUIREMENT.value)],
            "",
        ]
        return {"path": "00_Project_Index.md", "content": "\n".join(lines), "kind": "markdown"}

    def _assignment_checklist(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        requirement_nodes = context.nodes_by_type(NodeType.REQUIREMENT.value)
        task_nodes = context.nodes_by_type(NodeType.TASK.value)
        assignment_files = [
            node for node in context.nodes_by_type(NodeType.FILE.value) if node.get("properties", {}).get("file_type") == "assignment_notice"
        ]
        lines = [
            *frontmatter("Checklist", tags=["projectvault", "assignment"]),
            "# 과제 체크리스트",
            "",
            "## 과제 공지 출처",
            "",
            *markdown_links(context, assignment_files),
            "",
            "## 요구사항",
            "",
            *[f"- [ ] {context.link(node)}" for node in requirement_nodes],
            "",
            "## 할 일",
            "",
            *[f"- [ ] {context.link(node)}" for node in sorted(task_nodes, key=task_sort_key)],
            "",
        ]
        return {"path": "01_Assignment_Checklist.md", "content": "\n".join(lines), "kind": "markdown"}

    def _lecture_concepts(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        concept_nodes = context.nodes_by_type(NodeType.CONCEPT.value)
        lecture_files = [
            node for node in context.nodes_by_type(NodeType.FILE.value) if node.get("properties", {}).get("file_type") == "lecture_pdf"
        ]
        lines = [
            *frontmatter("ConceptIndex", tags=["projectvault", "lecture"]),
            "# 강의 개념",
            "",
            "## 강의자료 파일",
            "",
            *markdown_links(context, lecture_files),
            "",
            "## 개념",
            "",
            *[f"- {context.link(node)}" for node in concept_nodes],
            "",
        ]
        return {"path": "02_Lecture_Concepts.md", "content": "\n".join(lines), "kind": "markdown"}

    def _code_summary(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        code_files = [
            node for node in context.nodes_by_type(NodeType.FILE.value) if node.get("properties", {}).get("file_type") == "source_code"
        ]
        lines = [
            *frontmatter("CodeSummary", tags=["projectvault", "code"]),
            "# 코드 요약",
            "",
            "## 소스 파일",
            "",
        ]
        for file_node in code_files:
            lines.extend(
                [
                    f"### {context.link(file_node)}",
                    "",
                    f"- 관련 개념: {context.links(context.targets(file_node['id'], EdgeType.MENTIONS.value)) or '없음'}",
                    f"- 관련 할 일: {context.links(context.targets(file_node['id'], EdgeType.SUPPORTS.value, EdgeType.REQUIRES.value)) or '없음'}",
                    "",
                ]
            )
        return {"path": "03_Code_Summary.md", "content": "\n".join(lines), "kind": "markdown"}

    def _error_log(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        error_nodes = context.nodes_by_type(NodeType.ERROR.value)
        lines = [
            *frontmatter("ErrorLog", tags=["projectvault", "errors"]),
            "# 오류 로그",
            "",
        ]
        for error_node in error_nodes:
            files = context.targets(error_node["id"], EdgeType.OCCURS_IN.value)
            lines.extend(
                [
                    f"## {context.link(error_node)}",
                    "",
                    f"- 원인: {error_node.get('properties', {}).get('reason', '') or '알 수 없음'}",
                    f"- 관련 파일: {context.links(files) or '없음'}",
                    "",
                ]
            )
        if not error_nodes:
            lines.append("- 추출된 오류가 없습니다.")
        return {"path": "04_Error_Log.md", "content": "\n".join(lines), "kind": "markdown"}

    def _next_actions(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        task_nodes = sorted(context.nodes_by_type(NodeType.TASK.value), key=task_sort_key)
        lines = [
            *frontmatter("NextActions", tags=["projectvault", "tasks"]),
            "# 다음 할 일",
            "",
        ]
        for task_node in task_nodes:
            priority = task_node.get("properties", {}).get("priority", "MEDIUM")
            files = context.sources(task_node["id"], EdgeType.SUPPORTS.value, EdgeType.REQUIRES.value)
            requirements = context.targets(task_node["id"], EdgeType.DEPENDS_ON.value)
            lines.extend(
                [
                    f"- [ ] {context.link(task_node)}",
                    f"  - 우선순위: {priority}",
                    f"  - 관련 파일: {context.links(files) or '없음'}",
                    f"  - 요구사항: {context.links(requirements) or '없음'}",
                ]
            )
        if not task_nodes:
            lines.append("- 추출된 할 일이 없습니다.")
        lines.append("")
        return {"path": "05_Next_Actions.md", "content": "\n".join(lines), "kind": "markdown"}

    def _codex_context_pack(self, state: ProjectVaultState, context: "GraphNoteContext") -> dict[str, Any]:
        lines = [
            *frontmatter("ContextPack", tags=["projectvault", "codex"]),
            "# Codex 컨텍스트 팩",
            "",
            "Codex, Cursor 같은 AI 코딩 도구에 프로젝트 작업을 요청할 때 이 문서를 붙여넣으면 됩니다.",
            "",
            "## 프로젝트 스냅샷",
            "",
            f"- 입력 워크스페이스: `{state['input_dir']}`",
            f"- 스캔된 파일 수: {len(state['files'])}",
            f"- 그래프 노드 수: {len(state['graph_nodes'])}",
            f"- 그래프 엣지 수: {len(state['graph_edges'])}",
            "",
            "## 요구사항",
            "",
            *[f"- {node['label']}" for node in context.nodes_by_type(NodeType.REQUIREMENT.value)],
            "",
            "## 다음 할 일",
            "",
            *[f"- [{node.get('properties', {}).get('priority', 'MEDIUM')}] {node['label']}" for node in context.nodes_by_type(NodeType.TASK.value)],
            "",
            "## 중요 개념",
            "",
            *[f"- {node['label']}: {node.get('properties', {}).get('description', '')}" for node in context.nodes_by_type(NodeType.CONCEPT.value)],
            "",
            "## 파일",
            "",
            *[f"- {node['label']} ({node.get('properties', {}).get('file_type', 'document')})" for node in context.nodes_by_type(NodeType.FILE.value)],
            "",
            "## 경고",
            "",
            *([f"- {warning}" for warning in state["warnings"]] or ["- 없음"]),
            "",
            "## 보안 점검",
            "",
            f"- 발견 항목: {len(state.get('security_findings', []))}",
            "- 생성된 노트와 리포트에서 secret 값은 마스킹됩니다.",
            "",
        ]
        return {"path": "06_Codex_Context_Pack.md", "content": "\n".join(lines), "kind": "markdown"}

    def _file_note(self, state: ProjectVaultState, context: "GraphNoteContext", node: dict[str, Any]) -> dict[str, Any]:
        analysis = context.analysis_for_file_node(node)
        concept_nodes = context.targets(node["id"], EdgeType.MENTIONS.value)
        task_nodes = context.targets(node["id"], EdgeType.SUPPORTS.value, EdgeType.REQUIRES.value)
        lines = [
            *frontmatter("File", node_id=node["id"], tags=["projectvault", "file"]),
            f"# {node['label']}",
            "",
            "## 파일 경로",
            "",
            f"`{node.get('properties', {}).get('path', node['label'])}`",
            "",
            "## 역할 요약",
            "",
            str(analysis.get("summary", node.get("properties", {}).get("content_preview", ""))),
            "",
            "## 관련 개념",
            "",
            *(markdown_links(context, concept_nodes)),
            "",
            "## 관련 할 일",
            "",
            *(markdown_links(context, task_nodes, checkbox=True)),
            "",
        ]
        return {"path": context.note_path(node), "content": "\n".join(lines), "kind": "markdown"}

    def _concept_note(self, context: "GraphNoteContext", node: dict[str, Any]) -> dict[str, Any]:
        file_nodes = context.sources(node["id"], EdgeType.MENTIONS.value)
        related_tasks = related_tasks_for_files(context, file_nodes)
        lines = [
            *frontmatter("Concept", node_id=node["id"], tags=["projectvault", "concept"]),
            f"# {node['label']}",
            "",
            "## 설명",
            "",
            str(node.get("properties", {}).get("description", "")),
            "",
            "## 관련 파일",
            "",
            *markdown_links(context, file_nodes),
            "",
            "## 관련 할 일",
            "",
            *markdown_links(context, related_tasks, checkbox=True),
            "",
        ]
        return {"path": context.note_path(node), "content": "\n".join(lines), "kind": "markdown"}

    def _task_note(self, context: "GraphNoteContext", node: dict[str, Any]) -> dict[str, Any]:
        file_nodes = context.sources(node["id"], EdgeType.SUPPORTS.value, EdgeType.REQUIRES.value)
        concept_nodes = related_concepts_for_files(context, file_nodes)
        requirement_nodes = context.targets(node["id"], EdgeType.DEPENDS_ON.value)
        properties = node.get("properties", {})
        lines = [
            *frontmatter("Task", node_id=node["id"], tags=["projectvault", "task"]),
            f"# {node['label']}",
            "",
            "## 해야 할 일",
            "",
            node["label"],
            "",
            "## 왜 필요한가",
            "",
            str(properties.get("reason", "")),
            "",
            "## 관련 파일",
            "",
            *markdown_links(context, file_nodes),
            "",
            "## 관련 개념",
            "",
            *markdown_links(context, concept_nodes),
            "",
            "## 우선순위",
            "",
            str(properties.get("priority", "MEDIUM")),
            "",
            "## 관련 요구사항",
            "",
            *markdown_links(context, requirement_nodes),
            "",
        ]
        return {"path": context.note_path(node), "content": "\n".join(lines), "kind": "markdown"}

    def _error_note(self, context: "GraphNoteContext", node: dict[str, Any]) -> dict[str, Any]:
        file_nodes = context.targets(node["id"], EdgeType.OCCURS_IN.value)
        properties = node.get("properties", {})
        line_number = str(properties.get("line_number", "")).strip()
        redacted_excerpt = str(properties.get("redacted_excerpt", "")).strip()
        lines = [
            *frontmatter("Error", node_id=node["id"], tags=["projectvault", "error"]),
            f"# {node['label']}",
            "",
            "## 원인",
            "",
            str(node.get("properties", {}).get("reason", "")),
            "",
            "## 관련 파일",
            "",
            *markdown_links(context, file_nodes),
            "",
            "## 발견 위치",
            "",
            f"- File: {properties.get('source_file', '') or 'Unknown'}",
            f"- Line: {line_number or 'N/A'}",
            "",
            "## 마스킹된 근거",
            "",
            redacted_excerpt or "[REDACTED]",
            "",
        ]
        return {"path": context.note_path(node), "content": "\n".join(lines), "kind": "markdown"}

    def _decision_note(self, context: "GraphNoteContext", node: dict[str, Any]) -> dict[str, Any]:
        file_nodes = context.targets(node["id"], EdgeType.AFFECTS.value)
        lines = [
            *frontmatter("Decision", node_id=node["id"], tags=["projectvault", "decision"]),
            f"# {node['label']}",
            "",
            "## 결정 이유",
            "",
            str(node.get("properties", {}).get("reason", "")),
            "",
            "## 영향을 받는 파일",
            "",
            *markdown_links(context, file_nodes),
            "",
        ]
        return {"path": context.note_path(node), "content": "\n".join(lines), "kind": "markdown"}

    def _requirement_note(self, context: "GraphNoteContext", node: dict[str, Any]) -> dict[str, Any]:
        file_nodes = context.sources(node["id"], EdgeType.REQUIRES.value)
        task_nodes = context.sources(node["id"], EdgeType.DEPENDS_ON.value)
        lines = [
            *frontmatter("Requirement", node_id=node["id"], tags=["projectvault", "requirement"]),
            f"# {node['label']}",
            "",
            "## 요구사항",
            "",
            node["label"],
            "",
            "## 출처",
            "",
            str(node.get("properties", {}).get("source", "")),
            "",
            "## 관련 파일",
            "",
            *markdown_links(context, file_nodes),
            "",
            "## 의존하는 할 일",
            "",
            *markdown_links(context, task_nodes, checkbox=True),
            "",
        ]
        return {"path": context.note_path(node), "content": "\n".join(lines), "kind": "markdown"}


class GraphNoteContext:
    def __init__(self, state: ProjectVaultState) -> None:
        self.state = state
        self.nodes_by_id = {str(node["id"]): node for node in state["graph_nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in state["graph_edges"]:
            self.outgoing[str(edge["source"])].append(edge)
            self.incoming[str(edge["target"])].append(edge)
        self.note_paths = {node_id: self._note_path_for_node(node) for node_id, node in self.nodes_by_id.items()}
        self.analysis_by_path = {str(analysis.get("file_path", "")): analysis for analysis in state["analyzed_files"]}

    def nodes_by_type(self, node_type: str) -> list[dict[str, Any]]:
        return [node for node in self.state["graph_nodes"] if node.get("type") == node_type]

    def note_path(self, node: dict[str, Any]) -> str:
        return self.note_paths[str(node["id"])]

    def link(self, node: dict[str, Any]) -> str:
        path = self.note_path(node)
        target = path[:-3] if path.endswith(".md") else path
        return f"[[{target}|{node['label']}]]"

    def links(self, nodes: list[dict[str, Any]]) -> str:
        return ", ".join(self.link(node) for node in nodes)

    def targets(self, source_id: str, *relations: str) -> list[dict[str, Any]]:
        relation_set = set(relations)
        return [
            self.nodes_by_id[str(edge["target"])]
            for edge in self.outgoing.get(source_id, [])
            if str(edge.get("relation")) in relation_set and str(edge["target"]) in self.nodes_by_id
        ]

    def sources(self, target_id: str, *relations: str) -> list[dict[str, Any]]:
        relation_set = set(relations)
        return [
            self.nodes_by_id[str(edge["source"])]
            for edge in self.incoming.get(target_id, [])
            if str(edge.get("relation")) in relation_set and str(edge["source"]) in self.nodes_by_id
        ]

    def analysis_for_file_node(self, node: dict[str, Any]) -> dict[str, Any]:
        path = str(node.get("properties", {}).get("path", ""))
        return self.analysis_by_path.get(path, {})

    def _note_path_for_node(self, node: dict[str, Any]) -> str:
        node_type = str(node.get("type", ""))
        label = str(node.get("label", "note"))
        folder_by_type = {
            NodeType.FILE.value: "Files",
            NodeType.CONCEPT.value: "Concepts",
            NodeType.TASK.value: "Tasks",
            NodeType.ERROR.value: "Errors",
            NodeType.DECISION.value: "Decisions",
            NodeType.REQUIREMENT.value: "Requirements",
        }
        folder = folder_by_type.get(node_type, "Notes")
        return f"{folder}/{safe_filename(label)}.md"


def frontmatter(note_type: str, node_id: str | None = None, tags: list[str] | None = None) -> list[str]:
    fields: dict[str, Any] = {"type": note_type}
    if node_id:
        fields["node_id"] = node_id
    if tags:
        fields["tags"] = tags
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", ""])
    return lines


def markdown_links(context: GraphNoteContext, nodes: list[dict[str, Any]], checkbox: bool = False) -> list[str]:
    if not nodes:
        return ["- None"]
    prefix = "- [ ]" if checkbox else "-"
    return [f"{prefix} {context.link(node)}" for node in nodes]


def related_tasks_for_files(context: GraphNoteContext, file_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task_nodes: dict[str, dict[str, Any]] = {}
    for file_node in file_nodes:
        for task_node in context.targets(file_node["id"], EdgeType.SUPPORTS.value, EdgeType.REQUIRES.value):
            task_nodes[str(task_node["id"])] = task_node
    return list(task_nodes.values())


def related_concepts_for_files(context: GraphNoteContext, file_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    concept_nodes: dict[str, dict[str, Any]] = {}
    for file_node in file_nodes:
        for concept_node in context.targets(file_node["id"], EdgeType.MENTIONS.value):
            concept_nodes[str(concept_node["id"])] = concept_node
    return list(concept_nodes.values())


def task_sort_key(node: dict[str, Any]) -> tuple[int, str]:
    priority = str(node.get("properties", {}).get("priority", "MEDIUM")).upper()
    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(priority, 1)
    return rank, str(node.get("label", ""))


def type_label(node_type: str) -> str:
    label = NODE_TYPE_LABELS.get(node_type)
    return f"{label} ({node_type})" if label else node_type


def clean_generated_outputs(output_dir: Path) -> None:
    generated_files = {
        "00_Project_Index.md",
        "01_Assignment_Checklist.md",
        "02_Lecture_Concepts.md",
        "03_Code_Summary.md",
        "04_Error_Log.md",
        "05_Next_Actions.md",
        "06_Codex_Context_Pack.md",
        "GRAPH_REPORT.md",
        "graph.json",
        "sheets_rows.json",
    }
    generated_dirs = {"Concepts", "Files", "Tasks", "Errors", "Decisions", "Requirements"}

    for filename in generated_files:
        path = output_dir / filename
        if path.is_file():
            path.unlink()

    for dirname in generated_dirs:
        path = output_dir / dirname
        if not path.exists():
            continue
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()
