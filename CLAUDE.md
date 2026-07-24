# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 매 세션 시작 시 읽는 컨텍스트입니다.

## 프로젝트 개요

GitHub/GitLab push 이벤트를 감지해, 최신 커밋 기준으로 **변경된 디렉토리만** LLM으로 분석하여
디렉토리별 `README.md`(또는 `docs/{dir}.md`)를 자동 생성·수정하는 서비스.
브랜치별로 독립적으로 관리한다.

- 상태: 저장소 스캐폴딩 전 — 커밋 없음, 코드 없음. 아래 아키텍처/디렉토리 구조는 목표 설계이며 아직 구현되지 않았다.
  첫 작업은 대개 이 구조에 맞춰 `app/`, `prompts/`, `tests/`, `requirements.txt`, `.env.example` 등을 새로 만드는 것이다.
- 목표 단계: Phase 1 — 프롬프트 PoC
- 배포 대상: GCP e2-micro (무료 티어)
- 관련 프로젝트 아님: SSAFY 관광앱, BTC-ETH 트레이딩 시스템과는 무관한 별도 저장소

## 아키텍처 요약

```
Webhook 수신 (FastAPI) → BackgroundTask enqueue → diff 파싱(변경 디렉토리 추출)
  → 파일 내용 fetch (GitHub API) → LLM 호출 → md 생성/수정 → 봇 계정으로 커밋
```

세부 구조는 각 모듈 상단 docstring과 `app/` 디렉토리 자체를 참고할 것 — 이 파일에 코드를 복사해 넣지 않는다.

```
app/
├── webhook.py        # 수신 + HMAC 서명 검증
├── diff_parser.py     # push payload → 변경 디렉토리 목록
├── llm_client.py       # LLM 추상화 인터페이스 (Provider 교체 가능해야 함)
├── git_committer.py    # 결과 커밋/PR, [skip-docs] 태그 삽입
└── state.py            # SQLite, 브랜치별 마지막 처리 커밋 SHA
prompts/                # LLM 프롬프트 템플릿 (.txt), 코드에 하드코딩 금지
tests/
```

## 개발 명령어

아래는 목표 구조가 갖춰졌을 때 사용할 명령어다. `requirements.txt`/`app/`이 아직 없다면 먼저 아키텍처 요약에 맞게 스캐폴딩부터 한다.

```bash
# 의존성 설치
pip install -r requirements.txt

# 로컬 개발 서버
uvicorn app.main:app --reload --port 8000

# 테스트
pytest tests/ -v

# 특정 모듈만 테스트
pytest tests/test_diff_parser.py -v

# lint / format
ruff check app/
ruff format app/
```

## 코드 스타일

- Python 3.11+, type hint 필수 (함수 시그니처 전체)
- 비동기 I/O는 `async def` + `httpx.AsyncClient` 사용, `requests` 금지
- 커밋/PR 관련 로직에서 예외를 삼키지 말 것 — 반드시 로깅 후 재발생(re-raise)
- 새 외부 API 호출은 항상 `app/clients/`에 래퍼로 분리 (직접 fetch/httpx 호출 금지)

## 핵심 워크플로 규칙

1. **LLM Provider는 항상 `llm_client.py`의 인터페이스를 통해서만 호출한다.**
   Gemini → Claude 등 교체가 함수 하나로 끝나야 함. 특정 벤더 SDK를 다른 모듈에서 직접 import 금지.
2. **Webhook 핸들러는 절대 동기적으로 LLM 호출을 기다리지 않는다.**
   요청 즉시 202 응답 후 BackgroundTask/Cloud Tasks로 위임.
3. **무한 루프 방지**: 봇이 생성한 커밋 메시지에는 반드시 `[skip-docs]`를 포함시키고,
   webhook 수신 시 커밋 메시지에 `[skip-docs]`가 있으면 즉시 무시하고 리턴.
4. **기존 md 파일이 있는 디렉토리는 전체 재생성이 아니라 diff 기반 수정으로 프롬프트를 구성한다.**
5. **상태(state.py)는 브랜치별 마지막 처리 SHA만 저장한다.** 그 이상의 스키마 확장 금지(YAGNI).
6. 새 기능 추가 전 `tests/`에 실패하는 테스트부터 작성 (TDD 지향, 강제는 아님).

## 환경 변수

`.env.example` 참고. 절대 `.env`나 실제 키 값을 커밋하거나 CLAUDE.md에 붙여넣지 않는다.

- `GITHUB_WEBHOOK_SECRET`
- `GITHUB_BOT_TOKEN`
- `LLM_PROVIDER` (`gemini` | `claude` | `openai`)
- `LLM_API_KEY`

## 하지 말아야 할 것

- webhook payload 검증(HMAC) 없이 처리 로직 실행
- LLM 프롬프트를 코드 문자열로 하드코딩 (항상 `prompts/*.txt`에서 로드)
- 변경되지 않은 디렉토리까지 순회하며 md 재생성
- 이 CLAUDE.md에 코드 블록을 통째로 붙여넣어 문서화 대체하기 (파일 경로로 참조할 것)

## Claude에게 주는 참고

- 이 저장소는 1인 사이드 프로젝트이며 SSAFY 학업과 별개로 진행 중. 과도한 엔터프라이즈급 구조(마이크로서비스 분리 등) 제안 지양, GCP 무료 티어 제약을 항상 고려할 것.
- 모호한 요구사항은 Phase 1(프롬프트 품질) 우선순위로 판단할 것 — 자동화 파이프라인보다 md 결과물 품질이 이 프로젝트의 핵심 가치.
