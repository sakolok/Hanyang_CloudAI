"""Sample Gemini client wrapper.

The API key is read from the environment. No real key is stored in this file.
"""

from __future__ import annotations

import os


class GeminiClient:
    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def analyze_text(self, text: str) -> dict[str, str]:
        if not self.is_configured():
            return {
                "mode": "fake",
                "summary": "API key is not configured, so the sample returns a fake response.",
            }

        return {
            "mode": "configured",
            "summary": f"Would analyze {len(text)} characters with {self.model}.",
        }
