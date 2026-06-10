"""Discover files in a local input workspace."""

from __future__ import annotations

import logging
from pathlib import Path

from app.ingestors.pdf_ingestor import PdfIngestor
from app.schemas.file_item import FileItem

SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".pdf"}
PREVIEW_LIMIT = 300
ASSIGNMENT_DIR_NAMES = {"assignment", "assignments", "과제", "공지", "과제_및_공지", "과제및공지"}
LECTURE_DIR_NAMES = {"lecture_materials", "lecture", "lectures", "강의자료", "강의_자료", "수업자료", "수업_자료"}
CODE_DIR_NAMES = {"code", "src", "source", "코드", "소스코드", "소스_코드"}
NOTES_DIR_NAMES = {"notes", "note", "memo", "memos", "메모", "노트", "강의메모", "회의_메모"}
SUBMISSION_DIR_NAMES = {"submission", "submissions", "submit", "제출물", "제출", "보고서", "최종제출"}

logger = logging.getLogger(__name__)


def scan_input_folder(input_dir: str) -> list[dict[str, object]]:
    """Scan supported files and return structured dictionaries."""

    root = Path(input_dir).expanduser()
    if not root.exists():
        return []

    pdf_ingestor = PdfIngestor()
    scanned_files: list[dict[str, object]] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            continue

        warnings: list[str] = []
        content = ""
        try:
            if extension == ".pdf":
                content = pdf_ingestor.extract_text(path)
                if not content:
                    warnings.append(pdf_ingestor.warning_for_empty_text(path))
            else:
                content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warning = f"Could not read file as UTF-8: {path}"
            logger.warning(warning)
            warnings.append(warning)
        except Exception as exc:
            warning = f"Could not read file: {path} ({exc})"
            logger.warning(warning)
            warnings.append(warning)

        scanned_files.append(
            {
                "path": str(path),
                "filename": path.name,
                "extension": extension,
                "file_type": classify_file_type(path),
                "content": content,
                "content_preview": content[:PREVIEW_LIMIT],
                "warnings": warnings,
            }
        )

    return scanned_files


def classify_file_type(path: Path) -> str:
    normalized_parts = {part.lower() for part in path.parts}
    filename = path.name.lower()
    extension = path.suffix.lower()

    if normalized_parts & ASSIGNMENT_DIR_NAMES:
        return "assignment_notice"
    if normalized_parts & LECTURE_DIR_NAMES:
        return "lecture_pdf"
    if normalized_parts & CODE_DIR_NAMES or extension == ".py":
        return "source_code"
    if normalized_parts & NOTES_DIR_NAMES:
        return "note"
    if normalized_parts & SUBMISSION_DIR_NAMES:
        return "submission_file"
    if filename == "readme.md":
        return "readme"
    return "document"


class FileIngestor:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ingest(self) -> list[FileItem]:
        return [FileItem.from_dict(item, self.root) for item in scan_input_folder(str(self.root))]
