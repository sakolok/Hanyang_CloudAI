"""PDF text extraction."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PdfIngestor:
    """Extract text from text-based PDFs.

    Image-only PDFs and OCR are intentionally out of scope for the MVP.
    """

    def extract_text(self, path: Path) -> str:
        if path.suffix.lower() != ".pdf":
            return ""

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required to extract PDF text.") from exc

        reader = PdfReader(str(path))
        page_text = []
        for page in reader.pages:
            page_text.append(page.extract_text() or "")
        return "\n".join(page_text).strip()

    def warning_for_empty_text(self, path: Path) -> str:
        warning = f"PDF text is empty; image-based PDFs and OCR are not supported: {path}"
        logger.warning(warning)
        return warning
