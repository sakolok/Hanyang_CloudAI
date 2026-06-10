"""Gemini-backed structured file analysis."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import Settings
from app.prompts.extract_file_summary_prompt import EXTRACT_FILE_SUMMARY_PROMPT
from app.prompts.extract_tasks_prompt import EXTRACT_TASKS_PROMPT
from app.schemas.file_item import FileItem
from app.schemas.graph_item import FileAnalysisResult

logger = logging.getLogger(__name__)


def analyze_file(file_item: dict[str, object]) -> dict[str, object]:
    """Analyze one scanned file using Gemini when configured, otherwise fake output."""

    settings = Settings.from_env()
    extractor = GeminiExtractor(settings=settings, dry_run=False)
    return extractor.analyze_file(file_item)


class GeminiExtractor:
    def __init__(self, settings: Settings, dry_run: bool = True) -> None:
        self.settings = settings
        self.dry_run = dry_run

    def extract_summary(self, file_item: FileItem) -> dict[str, object]:
        analysis = self.analyze_file(file_item.to_dict())
        return {
            **analysis,
            "file": analysis["file_path"],
            "requirements": _titles(analysis.get("requirements", [])),
            "tasks": _titles(analysis.get("tasks", [])),
            "decisions": _titles(analysis.get("decisions", [])),
            "errors": _titles(analysis.get("errors", [])),
        }

    def analyze_file(self, file_item: dict[str, object]) -> dict[str, object]:
        if self.dry_run or not self.settings.gemini_api_key:
            return fake_analysis(file_item)

        try:
            payload = self._call_gemini(file_item)
            return parse_analysis_json(payload, file_item)
        except Exception as exc:
            logger.warning("Gemini analysis failed; using fallback result: %s", exc)
            return fallback_analysis(file_item, reason=str(exc))

    def _call_gemini(self, file_item: dict[str, object]) -> str:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise RuntimeError("langchain-google-genai and langchain-core are required.") from exc

        llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.gemini_api_key,
            temperature=0,
            retries=1,
            request_timeout=self.settings.gemini_timeout_seconds,
        )
        response = llm.invoke(
            [
                SystemMessage(content=f"{EXTRACT_FILE_SUMMARY_PROMPT}\n\n{EXTRACT_TASKS_PROMPT}"),
                HumanMessage(content=_format_file_for_prompt(file_item)),
            ]
        )
        return str(getattr(response, "content", response))


def fake_analysis(file_item: dict[str, object]) -> dict[str, object]:
    file_path = _file_path(file_item)
    file_type = str(file_item.get("file_type", "document"))
    filename = str(file_item.get("filename", file_path))

    result = FileAnalysisResult(
        file_path=file_path,
        file_type=file_type,
        summary=f"Fake analysis: {filename} 파일을 API 키 없이 시연용으로 구조화했습니다.",
    )

    if file_type == "assignment_notice":
        return FileAnalysisResult.from_dict(
            {
                **result.to_dict(),
                "requirements": [{"title": f"{filename}의 과제 요구사항 확인", "source": filename}],
                "tasks": [
                    {
                        "title": "제출 체크리스트 작성",
                        "priority": "HIGH",
                        "reason": "과제 공지에는 제출물, 분량, 기술 조건이 포함될 수 있습니다.",
                    }
                ],
            }
        ).to_dict()
    elif file_type == "source_code":
        return FileAnalysisResult.from_dict(
            {
                **result.to_dict(),
                "concepts": [{"name": "소스 코드", "description": "역할, 주요 함수, 보안 위험을 함께 검토해야 하는 코드 파일입니다."}],
                "tasks": [
                    {
                        "title": f"{filename}의 주요 함수와 실행 흐름 검토",
                        "priority": "MEDIUM",
                        "reason": "코드 파일은 프로젝트 맥락과 연결되어야 합니다.",
                    }
                ],
                "errors": [
                    {"title": "API 키 노출 가능성 점검", "reason": "코드와 설정 파일에 API 키가 하드코딩되어 있지 않은지 확인해야 합니다."}
                ],
            }
        ).to_dict()
    elif file_type == "lecture_pdf":
        return FileAnalysisResult.from_dict(
            {
                **result.to_dict(),
                "concepts": [
                    {"name": "강의 핵심 개념", "description": "강의자료 내용을 프로젝트 노트와 할 일 그래프에 재사용할 수 있도록 정리해야 합니다."}
                ],
            }
        ).to_dict()
    else:
        return FileAnalysisResult.from_dict(
            {
                **result.to_dict(),
                "tasks": [
                    {
                        "title": f"{filename}에서 프로젝트 맥락 정리",
                        "priority": "LOW",
                        "reason": "입력 워크스페이스에 포함된 자료입니다.",
                    }
                ],
            }
        ).to_dict()

    return result.to_dict()


def fallback_analysis(file_item: dict[str, object], reason: str = "JSON parsing failed") -> dict[str, object]:
    payload = fake_analysis(file_item)
    payload["summary"] = f"Fallback analysis for {_file_path(file_item)}. Reason: {reason}"
    return payload


def parse_analysis_json(raw_response: str, file_item: dict[str, object]) -> dict[str, object]:
    try:
        payload = json.loads(_strip_json_fence(raw_response))
        return _normalize_analysis(payload, file_item)
    except Exception as exc:
        logger.warning("Could not parse Gemini JSON response: %s", exc)
        return fallback_analysis(file_item, reason="Gemini returned invalid JSON")


def _normalize_analysis(payload: dict[str, Any], file_item: dict[str, object]) -> dict[str, object]:
    payload.setdefault("file_path", _file_path(file_item))
    payload.setdefault("file_type", str(file_item.get("file_type", "document")))
    payload.setdefault("summary", "")
    for key in ("concepts", "requirements", "tasks", "errors", "decisions"):
        payload.setdefault(key, [])
    return FileAnalysisResult.from_dict(payload).to_dict()


def _strip_json_fence(raw_response: str) -> str:
    text = raw_response.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    return fenced.group(1).strip() if fenced else text


def _format_file_for_prompt(file_item: dict[str, object]) -> str:
    content = str(file_item.get("content", ""))
    return json.dumps(
        {
            "file_path": _file_path(file_item),
            "filename": file_item.get("filename", ""),
            "extension": file_item.get("extension", ""),
            "file_type": file_item.get("file_type", "document"),
            "content": content[:20000],
        },
        ensure_ascii=False,
        indent=2,
    )


def _file_path(file_item: dict[str, object]) -> str:
    return str(file_item.get("path") or file_item.get("relative_path") or file_item.get("filename") or "")


def _titles(items: object) -> str:
    if not isinstance(items, list):
        return ""
    titles = []
    for item in items:
        if isinstance(item, dict) and item.get("title"):
            titles.append(str(item["title"]))
    return "; ".join(titles)
