"""File item schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FileItem:
    path: Path
    relative_path: Path
    filename: str
    extension: str
    file_type: str
    content: str = ""
    content_preview: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def category(self) -> str:
        return self.file_type

    @property
    def suffix(self) -> str:
        return self.extension

    @classmethod
    def from_dict(cls, item: dict[str, object], root: Path) -> "FileItem":
        path = Path(str(item["path"]))
        absolute_path = path if path.is_absolute() else (Path.cwd() / path).resolve()
        try:
            relative_path = absolute_path.relative_to(root.resolve())
        except ValueError:
            relative_path = Path(str(item["filename"]))

        return cls(
            path=absolute_path,
            relative_path=relative_path,
            filename=str(item["filename"]),
            extension=str(item["extension"]),
            file_type=str(item["file_type"]),
            content=str(item.get("content", "")),
            content_preview=str(item.get("content_preview", "")),
            warnings=list(item.get("warnings", [])),
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        payload["relative_path"] = self.relative_path.as_posix()
        return payload
