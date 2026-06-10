from __future__ import annotations

from pathlib import Path

from app.ingestors.file_ingestor import classify_file_type, scan_input_folder


def test_scan_input_folder_reads_supported_files(tmp_path: Path) -> None:
    assignment_dir = tmp_path / "assignment"
    lecture_dir = tmp_path / "lecture_materials"
    code_dir = tmp_path / "code"
    notes_dir = tmp_path / "notes"
    submission_dir = tmp_path / "submission"
    for directory in (assignment_dir, lecture_dir, code_dir, notes_dir, submission_dir):
        directory.mkdir()

    (assignment_dir / "notice.txt").write_text("과제 공지입니다.", encoding="utf-8")
    (lecture_dir / "week01.md").write_text("강의자료 메모입니다.", encoding="utf-8")
    (code_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (notes_dir / "memo.md").write_text("수업 메모입니다.", encoding="utf-8")
    (submission_dir / "answer.txt").write_text("제출 파일입니다.", encoding="utf-8")
    (tmp_path / "README.md").write_text("Project README", encoding="utf-8")
    (tmp_path / "ignored.json").write_text("{}", encoding="utf-8")

    scanned = scan_input_folder(str(tmp_path))

    assert len(scanned) == 6
    by_filename = {item["filename"]: item for item in scanned}
    assert by_filename["notice.txt"]["file_type"] == "assignment_notice"
    assert by_filename["week01.md"]["file_type"] == "lecture_pdf"
    assert by_filename["main.py"]["file_type"] == "source_code"
    assert by_filename["memo.md"]["file_type"] == "note"
    assert by_filename["answer.txt"]["file_type"] == "submission_file"
    assert by_filename["README.md"]["file_type"] == "readme"
    assert by_filename["notice.txt"]["content"] == "과제 공지입니다."
    assert by_filename["notice.txt"]["content_preview"] == "과제 공지입니다."
    assert "ignored.json" not in by_filename


def test_content_preview_is_limited_to_300_chars(tmp_path: Path) -> None:
    content = "a" * 350
    (tmp_path / "long.txt").write_text(content, encoding="utf-8")

    scanned = scan_input_folder(str(tmp_path))

    assert scanned[0]["content"] == content
    assert scanned[0]["content_preview"] == "a" * 300


def test_classify_file_type_rules() -> None:
    assert classify_file_type(Path("input_workspace/assignment/homework.md")) == "assignment_notice"
    assert classify_file_type(Path("input_workspace/과제_및_공지/기말프로젝트_공지.md")) == "assignment_notice"
    assert classify_file_type(Path("input_workspace/lecture_materials/week01.pdf")) == "lecture_pdf"
    assert classify_file_type(Path("input_workspace/강의자료/1주차_LangGraph.pdf")) == "lecture_pdf"
    assert classify_file_type(Path("input_workspace/code/app.txt")) == "source_code"
    assert classify_file_type(Path("input_workspace/코드/app.txt")) == "source_code"
    assert classify_file_type(Path("input_workspace/other/script.py")) == "source_code"
    assert classify_file_type(Path("input_workspace/notes/memo.txt")) == "note"
    assert classify_file_type(Path("input_workspace/메모/회의록.md")) == "note"
    assert classify_file_type(Path("input_workspace/submission/final.md")) == "submission_file"
    assert classify_file_type(Path("input_workspace/제출물/보고서초안.md")) == "submission_file"
    assert classify_file_type(Path("input_workspace/README.md")) == "readme"
    assert classify_file_type(Path("input_workspace/misc/spec.txt")) == "document"


def test_missing_pdf_does_not_fail_scan(tmp_path: Path) -> None:
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "memo.md").write_text("no pdf here", encoding="utf-8")

    scanned = scan_input_folder(str(tmp_path))

    assert len(scanned) == 1
    assert scanned[0]["extension"] == ".md"
