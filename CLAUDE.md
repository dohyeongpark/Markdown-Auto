# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 매 세션 시작 시 읽는 컨텍스트입니다.

## 프로젝트 개요

GitHub/GitLab push 이벤트를 감지해, 최신 커밋 기준으로 **변경된 디렉토리만** LLM으로 분석하여
디렉토리별 문서를 자동 생성·수정하는 서비스. 브랜치별로 독립적으로 관리한다.

생성된 문서는 **GitHub 저장소에 커밋하지 않고** 자체 DB(SQLite)에 저장하며, 같은 GCP 서버의
FastAPI 백엔드가 이를 REST API로 제공하고 Vue.js SPA가 프런트엔드로 노출한다.
(기존에 검토했던 "봇 계정으로 GitHub에 커밋" 방식은 폐기됨 — 아래 아키텍처 참고.)

- 상태: 백엔드/프런트엔드 스캐폴딩 완료, GCP e2-micro에 배포 완료, 웹훅 파이프라인 end-to-end 테스트 성공
  (VM 내부에서 만든 가짜 push payload 기준 — 실제 GitHub push로는 아직 미검증).
- 목표 단계: Phase 1 — 프롬프트 PoC
- 배포 대상: GCP e2-micro (무료 티어), 서버 1대에 백엔드+DB+프런트엔드 정적 파일을 모두 올림 (별도 서비스 분리 지양).
  실제 배포 정보는 아래 "배포 인프라" 절 참고.
- 관련 프로젝트 아님: SSAFY 관광앱, BTC-ETH 트레이딩 시스템(GCP 프로젝트 `parkdh0121`의 `statarb-vm`으로 추정)과는
  무관한 별도 저장소. 이 프로젝트는 별도 GCP 프로젝트·별도 결제 계정을 쓴다 (무료 티어 충돌 방지).

## 아키텍처 요약

```
Webhook 수신 (FastAPI) → BackgroundTask enqueue → diff 파싱(변경 디렉토리 추출)
  → 소스 파일 read-only fetch (GitHub API) → LLM 호출 → md 생성/수정
  → docs_store(SQLite)에 저장  ── (GitHub에는 쓰지 않음)

Vue.js SPA → FastAPI REST API(app/api.py) → docs_store 조회 → 문서 렌더링
```

세부 구조는 각 모듈 상단 docstring과 `app/` 디렉토리 자체를 참고할 것 — 이 파일에 코드를 복사해 넣지 않는다.

```
app/
├── main.py             # FastAPI 엔트리포인트, 라우터 연결 + 프런트엔드 정적 파일 서빙
├── webhook.py           # 수신 + HMAC 서명 검증
├── diff_parser.py        # push payload → 변경 디렉토리 목록
├── llm_client.py          # LLM 추상화 인터페이스 (Provider 교체 가능해야 함)
├── doc_writer.py          # LLM 결과를 docs_store에 저장 (과거 git_committer.py 역할 대체)
├── docs_store.py          # SQLite, 생성된 문서 본문 저장/조회 (repo/branch/directory 단위)
├── prompts.py              # 프롬프트 템플릿 렌더링 + 프리셋 레지스트리(PRESETS) + style_instructions 결합
├── prompt_store.py          # SQLite, repo/branch별 커스텀 프롬프트 설정(preset_id/custom_instructions)
├── api.py                 # 프런트엔드용 문서 목록/조회 + 프롬프트 설정 REST API
├── state.py                # SQLite, 브랜치별 마지막 처리 커밋 SHA
└── clients/
    ├── github.py            # 소스 파일 read-only fetch (커밋/PR 기능 없음)
    └── llm/                 # gemini.py / claude.py / openai.py — 벤더별 실제 호출
prompts/                 # LLM 프롬프트 템플릿 (.txt), 코드에 하드코딩 금지
├── generate_readme.txt / update_readme.txt  # 기본 생성/수정 템플릿
└── presets/               # 프리셋별 "추가 지침" 조각 (전체 템플릿 대체 아님) — educational.txt, concise.txt
frontend/                # Vue 3 + Vite SPA (Bootstrap 5 CSS만 사용, JS 번들은 미사용). 빌드 산출물을 app/main.py가 정적 서빙
tests/
```

## 배포 인프라

- GCP 프로젝트: `markdown-auto` (결제 계정 `0166C3-81EF15-95E5AE`, statarb-vm과 별개 — 무료 티어 안전).
  같은 결제 계정에 `gen-lang-client-0035780710`(Gemini API 키 발급용으로 추정) 프로젝트도 걸려 있으나 미사용.
- VM: `markdown-auto-vm`, zone `us-central1-a` (무료 티어 대상 리전), e2-micro, pd-standard 30GB, Debian 12
- 방화벽: `allow-app-8000` — tcp:8000 전체 공개 (0.0.0.0/0). 아직 HTTPS/도메인 미설정, 평문 HTTP만 사용.
  SSH(22)는 `allow-ssh-iap`로 IAP 전용(소스 `35.235.240.0/20`)만 허용 — `default-allow-ssh`/`default-allow-rdp`는
  전체 공개라 삭제함(2026-07-26). 반드시 아래처럼 `--tunnel-through-iap`로 접속할 것, 포트 22를 다시 공개하지 말 것.
- 배포 경로: VM의 `~/Markdown-Auto` (git clone), `~/Markdown-Auto/.venv`
- 서비스: systemd 유닛 `markdown-auto.service` (`uvicorn app.main:app --host 0.0.0.0 --port 8000`,
  `EnvironmentFile=~/Markdown-Auto/.env`), 부팅 시 자동 시작
- 배포 절차:
  1. 로컬에서 커밋·푸시
  2. `gcloud compute ssh markdown-auto-vm --project=markdown-auto --zone=us-central1-a --tunnel-through-iap --command="cd ~/Markdown-Auto && git pull && .venv/bin/pip install -r requirements.txt && sudo systemctl restart markdown-auto.service"`
  3. 프런트엔드 변경 시: 로컬에서 `npm run build` 후 `gcloud compute scp --recurse frontend/dist markdown-auto-vm:~/Markdown-Auto/frontend/dist --project=markdown-auto --zone=us-central1-a`
  4. `.env` 값 변경 시: 로컬 `.env`를 절대 채팅/로그에 붙여넣지 말고 `gcloud compute scp`로 직접 VM에 복사

## 트러블슈팅 / 배포 중 겪은 문제 (재발 방지)

- **시크릿을 URL 쿼리 파라미터로 보내지 말 것.** httpx는 요청 실패 시 요청 URL 전체를 예외 메시지에
  포함시키는데, 이를 그대로 로깅하면 시크릿이 서버 로그(journalctl 등)에 평문으로 남는다.
  실제로 Gemini API 키를 `?key=`로 보내다 이 사고가 발생했음 — 반드시 헤더로 보낼 것
  (`app/clients/llm/gemini.py`가 `x-goog-api-key` 헤더 사용 예시). 새 벤더 클라이언트 추가 시 동일하게 주의.
- **Gemini 모델은 특정 버전에 고정하지 말 것.** `gemini-2.0-flash`처럼 dated named model은 ListModels
  응답엔 남아있어도 generateContent 호출이 예고 없이 404로 retire될 수 있다. `gemini-flash-latest`처럼
  "현재 권장 모델"을 가리키는 alias를 기본값으로 쓴다.
- **한국(KRW) 결제 계정의 Gemini API는 quota가 아니라 "선불 크레딧" 방식이다.** 429가 떠도 요청 빈도
  제한이 아니라 계정 잔액 고갈일 수 있음 — 에러 메시지에 "prepayment credits are depleted"가 있으면
  AI Studio(ai.studio/projects)에서 잔액을 확인할 것.

## 개발 명령어

```bash
# 백엔드 의존성 설치
pip install -r requirements.txt

# 백엔드 로컬 개발 서버
uvicorn app.main:app --reload --port 8000

# 백엔드 테스트
pytest tests/ -v

# 특정 모듈만 테스트
pytest tests/test_diff_parser.py -v

# lint / format
ruff check app/
ruff format app/

# 프런트엔드 의존성 설치 + 개발 서버 (frontend/ 디렉토리에서)
npm install
npm run dev

# 프런트엔드 프로덕션 빌드 (app/main.py가 이 결과물을 정적 서빙)
npm run build
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
3. **생성된 문서는 GitHub에 커밋하지 않고 `docs_store.py`(SQLite)에만 저장한다.**
   이 설계 덕분에 봇이 자기 자신의 push를 다시 트리거하는 무한 루프 자체가 발생하지 않는다 —
   `[skip-docs]` 같은 자기 트리거 방지 로직을 되살릴 필요 없음.
4. **기존 문서가 있는 디렉토리는 전체 재생성이 아니라 diff 기반 수정으로 프롬프트를 구성한다.**
   기존 문서는 GitHub가 아니라 `docs_store.py`에서 조회한다.
5. **`state.py`는 브랜치별 마지막 처리 SHA만 저장한다.** 그 이상의 스키마 확장 금지(YAGNI).
   생성된 문서 본문은 `docs_store.py`, 커스텀 프롬프트 설정은 `prompt_store.py`의 별도 스키마(별도 SQLite 파일)에
   저장하며 서로 책임을 섞지 않는다.
6. **`app/clients/github.py`는 read-only다.** 소스 파일 fetch 용도로만 쓰고 커밋/PR 생성 기능을 다시 추가하지 않는다.
7. 새 기능 추가 전 `tests/`에 실패하는 테스트부터 작성 (TDD 지향, 강제는 아님).
8. **프롬프트 프리셋(`prompts/presets/*.txt`)은 전체 템플릿을 대체하지 않고, `generate_readme.txt`/
   `update_readme.txt` 렌더링 결과 뒤에 덧붙는 "추가 지침" 조각이다.** 프리셋 목록은 `app/prompts.py`의
   `PRESETS` 하드코딩 리스트로 관리한다 (파일시스템 스캔 방식 금지 — 솔로 프로젝트 규모에 과함, YAGNI).

## 환경 변수

`.env.example` 참고. 절대 `.env`나 실제 키 값을 커밋하거나 CLAUDE.md에 붙여넣지 않는다.

- `GITHUB_WEBHOOK_SECRET`
- `GITHUB_BOT_TOKEN` — read-only 권한이면 충분하다 (더 이상 커밋하지 않음)
- `LLM_PROVIDER` (`gemini` | `claude` | `openai`)
- `LLM_API_KEY`

## 하지 말아야 할 것

- webhook payload 검증(HMAC) 없이 처리 로직 실행
- LLM 프롬프트를 코드 문자열로 하드코딩 (항상 `prompts/*.txt`에서 로드)
- 변경되지 않은 디렉토리까지 순회하며 md 재생성
- 생성된 문서를 GitHub 저장소에 다시 커밋하기 (과거 설계, 폐기됨 — `docs_store.py`에 저장할 것)
- API 키/시크릿을 URL 쿼리 파라미터로 전달하기 (에러 로그에 평문 노출 위험 — 헤더 사용, 트러블슈팅 절 참고)
- 이 CLAUDE.md에 코드 블록을 통째로 붙여넣어 문서화 대체하기 (파일 경로로 참조할 것)

## Claude에게 주는 참고

- 이 저장소는 1인 사이드 프로젝트이며 SSAFY 학업과 별개로 진행 중. 과도한 엔터프라이즈급 구조(마이크로서비스 분리 등) 제안 지양, GCP 무료 티어 제약을 항상 고려할 것.
- 모호한 요구사항은 Phase 1(프롬프트 품질) 우선순위로 판단할 것 — 자동화 파이프라인보다 md 결과물 품질이 이 프로젝트의 핵심 가치.
