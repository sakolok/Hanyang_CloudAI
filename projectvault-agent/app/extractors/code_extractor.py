"""Lightweight code signal extraction."""

from __future__ import annotations

from app.schemas.file_item import FileItem


CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".go", ".rs"}


class CodeExtractor:
    def extract(self, file_item: FileItem) -> dict[str, str]:
        if file_item.suffix not in CODE_SUFFIXES:
            return {"code_language": "", "code_signals": ""}

        return {
            "code_language": file_item.suffix.lstrip("."),
            "code_signals": "Code file discovered for later static analysis.",
        }

