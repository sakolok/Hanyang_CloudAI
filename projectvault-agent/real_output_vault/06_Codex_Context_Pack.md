---
type: "ContextPack"
tags: ["projectvault", "codex"]
---

# Codex 컨텍스트 팩

Codex, Cursor 같은 AI 코딩 도구에 프로젝트 작업을 요청할 때 이 문서를 붙여넣으면 됩니다.

## 프로젝트 스냅샷

- 입력 워크스페이스: `/Users/kang-ok-il/Documents/Hanyang_AI_cloud/projectvault-agent/real_course_input`
- 스캔된 파일 수: 8
- 그래프 노드 수: 67
- 그래프 엣지 수: 114

## 요구사항

- 보고서는 팀원 정보, AI 에이전트의 필요성/목적/개요, 워크플로우 설명, 실행 예시, 구현 방법 설명을 포함해야 함
- 보고서는 최소 A4 5페이지 이상 작성해야 함
- 소스코드는 LangChain/LangGraph를 사용하여 에이전트를 구현해야 함
- API 키가 노출되지 않도록 주의해야 함
- 팀원 중 1인만 과제 제출란에 업로드해야 함
- AI 사용 흔적을 남기지 않아야 함
- 백엔드 소스코드 제출
- 보고서에 서버 세팅 방법 설명 포함
- 보고서에 실행 예시 (스크린샷 등) 포함
- API 키를 비워놓고 제출 (예: "YOUR-API-KEY-HERE"로 대체)
- 조교가 설치할 수 있도록 필요한 준비사항 설명
- AI 에이전트 응용 프로그램 개발
- 팀원 1~3인으로 구성
- 평가 시 아이디어 70%, 구현 완성도 30% 반영
- 기말 프로젝트 팀 활동 수행
- 6월 12일까지 기말 프로젝트 제출

## 다음 할 일

- [HIGH] 보고서에 AI 에이전트의 실행 예시(입력 및 출력)를 추가하여 의도대로 동작함을 보여주기
- [HIGH] LangChain/LangGraph를 사용하여 AI 에이전트 소스코드 구현하기
- [HIGH] 보고서에 설계한 워크플로우와 그에 대한 설명을 작성하기
- [HIGH] API 키가 소스코드에 노출되지 않도록 처리하기
- [HIGH] 보고서에 서버 (패키지 등) 세팅 방법 작성
- [HIGH] 보고서에 실행 예시 (스크린샷 등) 추가
- [HIGH] 제출 전 API 키를 비워두거나 대체 문자열로 변경
- [HIGH] 조교를 위한 설치 준비사항 문서화
- [HIGH] 기말 프로젝트 제출 준비 및 완료
- [HIGH] 실행 예시 입력/출력 추가
- [MEDIUM] 입력 폴더 스캔
- [MEDIUM] 파일 내용 분석
- [MEDIUM] 요구사항/개념/할 일/오류/결정사항 추출
- [MEDIUM] 경량 그래프 생성
- [MEDIUM] Obsidian Markdown 노트 생성
- [MEDIUM] Google Sheets 요약 row 생성
- [MEDIUM] 최종 리포트 생성

## 중요 개념

- Few-shot 프롬프팅: 예시를 몇 개 보여주어 특정 형식이나 패턴을 모델에게 제시하는 기법
- Chain of Thought (CoT): 풀이 과정을 나열하여 모델의 논리적 추론 능력을 활성화하고 정답률을 높이는 기법
- Zero-shot CoT: "차례대로 풀자"와 같은 특정 문구로 예시 없이 추론 능력을 유도하는 기법
- Least-to-Most: 문제를 하위 문제로 쪼개어 복잡한 다단계 문제를 해결하는 기법
- Self-Consistency: 여러 답을 생성하고 다수결 투표를 통해 답변의 신뢰성과 정확도를 검증하는 기법
- LangChain: 거대 언어 모델을 사용하여 에이전트 애플리케이션을 쉽게 구축할 수 있도록 돕는 오픈 소스 프레임워크
- Chains (LangChain): LLM 호출, 데이터 처리 등 여러 작업을 순차적으로 연결하는 시퀀스를 정의하는 구성 요소
- Agents (LangChain): LLM을 추론 엔진으로 사용하여 어떤 행동을 취할지, 어떤 도구를 사용할지 동적으로 결정하는 구성 요소
- Prompts (LangChain): LLM에 입력할 지시사항을 포맷팅하고 관리하는 구성 요소
- Retrieval (LangChain): 외부 데이터를 로드하고 검색하여 LLM에 제공할 수 있도록 벡터DB 또는 API를 제공하는 구성 요소 (RAG 구현 시 필수)
- Memory (LangChain): 대화의 맥락을 유지하기 위해 이전 상호작용 데이터를 저장하고 관리하는 구성 요소
- Models (LangChain): LLM(텍스트 생성) 및 Chat Models(대화형 메시지 처리)에 대한 표준 인터페이스를 제공하는 구성 요소
- LCEL Chain: LangChain의 표현식 언어로, 파이프(|) 연결을 통해 선형 흐름에 최적화된 구조
- LangGraph: 노드-엣지 그래프 구조로 비선형 흐름, 조건 분기, 순환/반복(Loop)을 자유롭게 표현할 수 있는 프레임워크
- StateGraph: LangGraph의 핵심으로, 클래스를 명시적으로 선언하여 자료구조를 줄 수 있으며 그래프 실행 중 상태가 자동 전달되는 구조
- Obsidian 시각적 그래프: 할 일 및 정보 간의 관계를 시각적으로 표현하여 관리하는 도구
- Google Sheets 연동: 추출된 정보를 요약하여 일정 관리에 활용하기 위한 스프레드시트 통합
- Requirement 노드: 과제 공지사항 등에서 추출된 요구사항을 나타내는 그래프 노드
- Task 노드: 수행해야 할 구체적인 할 일을 나타내는 그래프 노드

## 파일

- 강의자료/강의메모.md (lecture_pdf)
- 과제_및_공지/기말프로젝트_공지.md (assignment_notice)
- 과제_및_공지/제출안내.md (assignment_notice)
- 과제_및_공지/평가기준.md (assignment_notice)
- 메모/LMS_확인_메모.md (note)
- 메모/내_정리.md (note)
- 제출물/README.md (submission_file)
- 제출물/보고서_초안.md (submission_file)

## 경고

- 없음

## 보안 점검

- 발견 항목: 0
- 생성된 노트와 리포트에서 secret 값은 마스킹됩니다.
