# ProjectVault Agent

ProjectVault Agent는 LMS에서 확인한 과제 공지, 제출 안내, 강의자료, 메모를 입력 폴더에 저장하면 이를 분석해 Obsidian 작업공간, 할 일 그래프, Google Sheets 요약표로 정리해 주는 로컬 에이전트입니다.

## 프로젝트 개요

교류수학처럼 여러 학교의 LMS를 확인해야 하는 경우, 공지와 과제 조건, 제출 안내, 강의자료를 놓치기 쉽습니다. 이 프로젝트는 사용자가 LMS에서 필요한 내용을 한 번에 스크랩해 입력 폴더에 저장하고, 이후에는 Obsidian과 Google Sheets에서 과제 요구사항과 할 일을 계속 확인할 수 있도록 만들었습니다.

현재 구현은 LMS에 자동 로그인하거나 공지를 자동 수집하지 않습니다. 학교별 LMS 구조와 로그인 방식이 다르고 개인정보 및 인증 문제가 생길 수 있기 때문에, MVP에서는 사용자가 직접 스크랩한 자료를 입력으로 사용합니다.

## 주요 기능

- 입력 폴더의 `.txt`, `.md`, `.py`, `.pdf` 파일 스캔
- 과제 공지, 제출 안내, 강의자료, 메모, 제출물 초안 분류
- Gemini API를 이용한 요구사항, 핵심 개념, 할 일, 결정사항, 오류 기록 추출
- `Project`, `File`, `Concept`, `Task`, `Error`, `Decision`, `Requirement` 기반 경량 그래프 생성
- Obsidian Markdown 노트와 `[[wikilink]]` 생성
- `graph.json` 생성
- Google Sheets 요약표 append 및 `sheets_rows.json` local fallback 저장

## 입력 폴더 구조

기본 입력 폴더는 다음과 같이 구성합니다.

```text
input_workspace/
├── 과제_및_공지/
├── 강의자료/
├── 코드/
├── 메모/
└── 제출물/
```

실제 입력 예시는 다음과 같은 형태로 구성할 수 있습니다.

| 폴더명 | 파일 유형 | 예시 파일 |
| --- | --- | --- |
| `과제_및_공지` | `assignment_notice` | `기말프로젝트_공지.md`, `제출안내.md`, `평가기준.md` |
| `강의자료` | `lecture_pdf` | `강의메모.md`, 강의 PDF 파일 |
| `메모` | `note` | `LMS_확인_메모.md`, `내_정리.md` |
| `제출물` | `submission_file` | `보고서_초안.md`, `README.md` |

프로그래밍 과제의 경우에는 선택적으로 `코드` 폴더를 추가하여 `.py` 파일도 함께 분석할 수 있습니다. 영어 폴더명(`assignment/`, `lecture_materials/`, `code/`, `notes/`, `submission/`)도 지원합니다.

## 출력 폴더 구조

`write` 모드로 실행하면 지정한 출력 폴더에 다음 파일들이 생성됩니다.

```text
output_vault/
├── 00_Project_Index.md
├── 01_Assignment_Checklist.md
├── 02_Lecture_Concepts.md
├── 03_Code_Summary.md
├── 04_Error_Log.md
├── 05_Next_Actions.md
├── Concepts/
├── Files/
├── Tasks/
├── Errors/
├── Decisions/
├── Requirements/
├── graph.json
├── sheets_rows.json
└── GRAPH_REPORT.md
```

주요 확인 파일은 다음과 같습니다.

- `00_Project_Index.md`: 전체 작업공간의 시작 페이지
- `01_Assignment_Checklist.md`: 과제 공지와 제출 조건 정리
- `02_Lecture_Concepts.md`: 강의자료에서 추출한 핵심 개념
- `05_Next_Actions.md`: 우선순위가 있는 다음 할 일 목록
- `graph.json`: 노드와 엣지 기반의 경량 그래프 데이터
- `sheets_rows.json`: Google Sheets에 저장할 요약 row의 local fallback 파일

## Obsidian 확인 방법

생성된 Markdown 노트와 wikilink를 편하게 보려면 Obsidian 프로그램이 필요합니다.

1. Obsidian을 설치합니다.
2. Obsidian에서 `Open folder as vault`를 선택합니다.
3. 실행 결과로 생성된 출력 폴더를 선택합니다.
4. `00_Project_Index.md`를 열면 전체 노트 구조를 확인할 수 있습니다.
5. Graph View를 열면 요구사항, 할 일, 파일, 개념 사이의 연결을 시각적으로 볼 수 있습니다.

Obsidian을 설치하지 않아도 Markdown 파일 자체는 일반 텍스트 편집기로 열 수 있지만, `[[wikilink]]`와 그래프 뷰를 활용하려면 Obsidian에서 여는 것이 좋습니다.

## 설치 방법

Python 3.10 이상을 권장합니다.

```bash
pip install -r requirements.txt
```

설치 후 테스트는 다음 명령으로 확인합니다.

```bash
python -m pytest -q
```

테스트는 Gemini API 키나 Google Sheets 인증정보가 없어도 통과하도록 구성되어 있습니다.

## 환경변수 설정 방법

`.env.example`을 복사해 `.env`를 만들고 필요한 값만 채웁니다.

```bash
cp .env.example .env
```

기본 예시는 다음과 같습니다.

```env
GEMINI_API_KEY=
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30

GOOGLE_SHEETS_ENABLED=false
GOOGLE_SHEETS_SPREADSHEET_ID=
GOOGLE_SHEETS_RANGE=ProjectVault!A:I
GOOGLE_SHEETS_TIMEOUT_SECONDS=60
GOOGLE_SHEETS_RETRIES=2
GOOGLE_SHEETS_CREDENTIALS_FILE=
```

## Gemini API 설정 방법

Gemini 분석을 실제로 사용하려면 `.env`에 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`를 설정합니다.

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

API 키가 없으면 fake extractor가 sample output을 반환합니다. 이 경우 전체 workflow와 테스트는 동작하지만, 실제 입력 자료를 기반으로 한 Gemini 분석은 수행되지 않습니다.

## Google Sheets API 설정 방법

Google Sheets 저장은 선택 기능입니다. 설정하지 않아도 `sheets_rows.json`으로 local fallback 저장됩니다.

Google Sheets 연동 순서는 다음과 같습니다.

1. Google Cloud Console에서 프로젝트를 생성하거나 선택합니다.
2. `API 및 서비스` → `라이브러리`에서 Google Sheets API를 검색해 활성화합니다.
3. `IAM 및 관리자` → `서비스 계정`에서 서비스 계정을 생성합니다.
4. 서비스 계정의 `키` 탭에서 JSON 키를 생성합니다.
5. 생성한 JSON 파일은 별도 위치에 보관합니다.
6. JSON 파일 안의 `client_email` 값을 확인합니다.
7. Google Sheets에서 사용할 스프레드시트를 만들고, 오른쪽 위 `공유` 버튼을 누릅니다.
8. 서비스 계정의 `client_email`을 추가하고 `편집자` 권한을 부여합니다.
9. 시트 하단 탭 이름을 `ProjectVault`로 만들거나, `.env`의 range를 실제 탭 이름에 맞게 수정합니다.
10. 스프레드시트 URL에서 `/d/`와 `/edit` 사이의 값을 복사해 `GOOGLE_SHEETS_SPREADSHEET_ID`에 넣습니다.

`.env` 설정 예시는 다음과 같습니다.

```env
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
GOOGLE_SHEETS_RANGE=ProjectVault!A:I
GOOGLE_SHEETS_CREDENTIALS_FILE=/path/to/projectvault-service-account.json
GOOGLE_SHEETS_TIMEOUT_SECONDS=90
GOOGLE_SHEETS_RETRIES=3
```

실행 후 `Sheets status: google-sheets`가 나오면 Google Sheets append가 성공한 것입니다. 인증정보가 없거나 네트워크 문제로 저장에 실패하면 workflow는 중단되지 않고 출력 폴더에 `sheets_rows.json`을 생성합니다.

## dry-run 실행 방법

`dry-run`은 외부 Google Sheets 저장을 하지 않고, 전체 workflow가 어떻게 동작하는지 확인하는 모드입니다.

```bash
python -m app.main --input ./data/sample_project --output ./output_vault --mode dry-run
```

## write 모드 실행 방법

`write` 모드는 Obsidian 노트, `graph.json`, `sheets_rows.json`, `GRAPH_REPORT.md`를 실제 출력 폴더에 생성합니다.

```bash
python -m app.main --input ./data/sample_project --output ./output_vault --mode write
```

실제 과목 자료 예시를 실행하려면 입력과 출력 경로를 바꿔 실행합니다.

```bash
python -m app.main --input ./real_course_input --output ./real_output_vault --mode write
```

## 실행 결과 예시

샘플 프로젝트 기준 실행 예시는 다음과 같습니다.

```text
ProjectVault Agent initialized
Input path: .../data/sample_project
Output path: .../output_vault
Mode: write
Files discovered: 9
Analyzed files: 9
Graph nodes: 22
Graph edges: 26
Obsidian files planned: 31
Sheets rows prepared: 22
Sheets status: local-fallback
Warnings: 1
```

확인할 주요 산출물은 다음과 같습니다.

- `output_vault/00_Project_Index.md`
- `output_vault/01_Assignment_Checklist.md`
- `output_vault/05_Next_Actions.md`
- `output_vault/graph.json`
- `output_vault/sheets_rows.json`
- `output_vault/GRAPH_REPORT.md`

## 테스트

```bash
python -m pytest -q
```

테스트 범위는 다음과 같습니다.

- 입력 폴더 스캔
- PDF 텍스트 추출 가능한 파일 처리
- Gemini fake/fallback extractor
- LangGraph workflow
- graph.json exporter
- Obsidian exporter
- Google Sheets local fallback
- secret scanner와 redaction

## 한계점

- LMS 자동 로그인과 자동 크롤링은 지원하지 않습니다.
- 이미지 기반 PDF와 스캔 PDF OCR은 지원하지 않습니다.
- 현재는 사용자가 `.md`나 `.txt` 파일을 직접 입력 폴더에 넣어야 합니다.
- 입력 자료가 많아지면 Obsidian 그래프의 가시성이 떨어질 수 있습니다.
- Google Sheets는 append 중심이며, 기존 row 업데이트나 중복 정리는 제한적입니다.

## 향후 개선 방향

- 여러 학교 또는 여러 과목을 구분해서 관리할 수 있는 workspace 지원
- 공지와 과제를 쉽게 추가할 수 있는 프론트 화면 또는 실행 프로그램 환경 구성
- 마감일 추출 및 Google Calendar 연동
- OCR 기반 이미지 PDF 및 스캔 PDF 처리
- 자료가 많아졌을 때를 위한 할 일 필터링, 중복 병합, 그래프 가시성 개선
- 학교별 LMS export/import 방식 지원
