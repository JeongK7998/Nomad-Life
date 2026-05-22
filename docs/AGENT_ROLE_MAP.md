# Agent Role Map

Nomad Life의 최종 핵심은 Dashboard다. 다만 Dashboard는 단순 차트 모음이 아니라 하위 에이전트들이 각자의 책임을 명확히 가진 뒤 Coordinator가 이를 조율한 결과여야 한다.

현재 단계의 목표는 세부 기능을 완성하는 것이 아니라, Hermes의 역할과 샘플 하위 에이전트가 어떤 입력을 읽고 어떤 판단을 Dashboard에 제공하는지 검증하는 것이다.

## Dashboard-First Principle

Dashboard는 다음 질문에 답해야 한다.

- 나는 오늘/이번 주 어떤 활동에 시간을 많이 쓰고 있는가?
- 각 활동의 누적량은 어떻게 변하고 있는가?
- 의도한 집중과 실제 비중이 어긋나는 영역은 어디인가?
- 일정, 운동, 영어, 재정, 회복 상태가 서로 충돌하고 있는가?
- 지금 당장 실행할 것보다 조율이 필요한 것은 무엇인가?

초기 Dashboard는 완성된 정량 분석보다 신뢰 가능한 방향성을 우선한다.

```txt
Raw Capture / Local Context
        ↓
Domain Agent Interpretation
        ↓
Coordinator Synthesis
        ↓
Dashboard Metrics / Brief / Candidate Signals
```

## Hermes Role

Hermes는 앱도, 단순 챗봇도 아니다. Hermes는 다음 역할을 갖는 runtime이다.

- AGENTS.md와 Skill 문서를 읽고 프로젝트 원칙을 유지한다.
- 로컬 deterministic script를 도구처럼 사용한다.
- 하위 에이전트의 입력/출력 계약을 조율한다.
- 불확실한 데이터는 불확실하다고 표시한다.
- 민감한 외부 앱 수정은 승인 전에는 수행하지 않는다.
- Dashboard가 읽을 수 있는 report, JSON, candidate를 만든다.
- 사용자와의 대화는 Coordinator를 통해 하나의 응답으로 제공한다.

Hermes가 직접 해야 하는 일:

- 맥락 해석
- 우선순위 조율
- 하위 에이전트 결과 종합
- Dashboard narrative 생성
- 다음 질문/후속 입력 제안

Hermes가 초기에는 직접 하지 말아야 하는 일:

- 캘린더/메모/가계부/소셜 계정 수정
- 자동 결제, 자동 게시, 자동 일정 변경
- 사용자의 모든 목표를 강제하는 운영
- 불안정한 외부 연동을 source of truth로 삼는 것

## Primary Activity Dashboard Model

사용자가 직접 입력하는 capture의 큰 부분은 활동 시간 기록이 될 가능성이 높다.

예시:

```txt
9시부터 11시까지 코딩
오후 3시부터 1시간 수영
저녁에 영어 40분
오늘 헬스 등 운동 45분, 스쿼트 5세트
```

따라서 Dashboard의 기초 축은 activity allocation이다.

초기 축:

- AI Work
- Health
- English
- Finance
- Schedule
- Rest
- Creator/Social
- Travel/Experience

핵심 지표:

- 오늘 활동 시간
- 주간 누적 시간
- 영역별 비중
- 일정 밀도
- 운동 빈도와 종류
- 영어 학습 시간과 학습 자료 수
- 재정 데이터 freshness
- 소셜/콘텐츠 지표 freshness

## Agent Priority

| Agent | Priority | Current Role | Input Source | Dashboard Output | Integration Status |
| --- | --- | --- | --- | --- | --- |
| Coordinator | P0 | 전체 조율과 단일 응답 | 모든 context/report | 오늘/주간 운영안 | active |
| Schedule | P0 | 일정 밀도와 시간 제약 제공 | Apple Calendar context | schedule density, time pressure | Calendar read-only active |
| Health | P1 | 운동 시간/종류/근력 세부/회복 신호 정리 | capture, structured workout form, future Apple Health export | health time, workout mix, body-part interval, strength progression, recovery signal | thin report active |
| Finance | P1 | 외부 가계부 데이터를 읽고 지출 압력과 패턴 분석 | existing finance app export/download or read-only view | spend status, budget pressure, trend/risk commentary | read-only importer pending |
| English | P1 | 누적 영어 학습 리뷰를 해석하고 반복 issue를 추적 | GPTs review JSON/MD, capture, iCloud transcript folder later | learning profile, issue tracker, recurrence checks, pre-study context | thin agent active |
| Rest | P2 | 과부하와 회복 여지 조율 | capture, schedule, health | recovery vs productivity | conceptual |
| UX Flow Review | P2 | 전체 사용자 흐름 검증 | URL, screenshots, dashboard data, user scenario | UX flow findings | documented validation skill |
| GUI Review | P2 | 레이아웃/비주얼 구현 품질 검증 | screenshots, CSS/HTML/JS, design tokens | GUI findings | documented validation skill |
| Review Value Review | P2 | 리뷰 콘텐츠 가치와 정보 밀도 검증 | dashboard JSON, reports, rendered review cards | content value findings | documented validation skill |
| Creator/Social | P3 | 콘텐츠 업로드/조회수 raw data 확인 | future social export/API | content output, view trends | defer |
| AI Work | P3 | AI 작업 방식과 산출물 정리 | capture, future git/Codex logs | work blocks, output signal | undefined, evolve slowly |

## Sample Sub-Agent Thin Slice

샘플 하위 에이전트는 복잡한 자동화를 하지 않고, 다음만 검증한다.

1. 관련 capture/context를 읽는다.
2. 해당 영역의 신호를 요약한다.
3. Dashboard에 올릴 수 있는 최소 지표를 만든다.
4. Coordinator가 그 결과를 하나의 운영 제안으로 조율한다.

추천 샘플:

- `nomad-health`: 사용자가 직접 남긴 운동 기록을 읽고 시간/운동 종류/빈도를 요약한다.
- `nomad-english`: iCloud에 저장된 텍스트 학습 기록 또는 capture를 읽고 학습 시간/진도 후보를 요약한다.
- `nomad-calendar-context`: 이미 동작 중인 Schedule context로 일정 밀도를 제공한다.

Current implementation:

- `scripts/generate_agent_reports.py` creates thin Health and English reports.
- Shared Coordinator input lives at `data/agent_reports/YYYY-MM-DD.json` and `data/context/agent-reports.json`.
- Coordinator reads agent reports before falling back to raw capture-count summaries.
- These reports are capture-based interpretation candidates, not autonomous agents with external app permissions.

## Validation Agent Layer

UX 검증은 매번 임시 프롬프트로 수행하지 않고 고정 Skill로 유지한다.

Validation agents:

- `nomad-ux-flow-review`: task flow, navigation, save/error/approval feedback, mobile usability.
- `nomad-gui-review`: layout breakage, spacing, responsive behavior, visual artifacts, Design System alignment.
- `nomad-review-value-review`: review content density, repetition, scanability, whole-picture usefulness.

These agents are advisory. Coordinator synthesizes their findings into fix-now, defer, ask-user, or document decisions.

Detailed protocol lives in `docs/UX_VALIDATION_AGENTS.md`.

## External Integration Boundaries

### Apple Health

Apple Health 접근은 민감 데이터다. 초기에는 직접 HealthKit 연동을 하지 않고, 가능한 경우 export 파일 또는 사용자가 명시적으로 저장한 기록부터 사용한다.

HealthKit 직접 연동은 별도 승인 후 진행한다.

### Structured Workout Form

근력운동은 Quick Capture보다 구조화 폼이 적합하다.

초기 원칙:

- Cockpit 또는 iPhone 홈 화면 진입으로 workout detail form을 연다.
- Quick Capture의 `근력운동 시작` 같은 입력은 form 진입 트리거 또는 session 후보로 해석할 수 있다.
- 세부 기록은 `data/health/workout-sessions.jsonl`에 저장한다.
- 저장 시 요약 capture도 남겨 audit trail을 유지한다.
- Health Agent는 부위별 빈도, 운동별 무게/반복/세트 변화, 부위별 휴식 간격을 분석하는 방향으로 확장한다.

### Finance Supabase

개인 가계부가 Supabase 서버를 사용한다면 최종적으로 read-only 접근 또는 export 자동화가 이상적이다.

초기 원칙:

- 가계부 입력은 기존 개인 앱에서 계속 한다.
- Nomad Life는 지출 입력 UI가 아니라 read-only 분석자다.
- 지출 내역은 다른 앱에서 주기적으로 download/export하거나 read-only view로 가져온다.
- Supabase credential/API 접근은 별도 승인 후 진행한다.
- 어렵다면 정해진 export 파일을 자동 다운로드하거나 로컬 폴더에 두는 방식을 먼저 검토한다.

### Finance JSON Export Fallback

가계부 앱 또는 서버에 안정적인 read-only 접근이 어렵다면, 사용자가 매일 JSON export를 내려받아 iCloud Drive 또는 local inbox에 넣는 방식을 정식 fallback으로 둔다.

초기 원칙:

- JSON export는 `data/expenses/imports/inbox/`로 가져와 normalized expense contract로 변환한다.
- 현재 원본 export 폴더는 `/Users/jongiljeong/Library/Mobile Documents/com~apple~CloudDocs/Nomad_life/Finance`다.
- iCloud Drive finance export 폴더는 primary database가 아니라 read-only dropbox다.
- importer는 원본 JSON을 수정하지 않고, 처리 후 local processed 폴더로 복사하거나 이동한다.
- 초기 importer는 `scripts/import_finance_exports.py`이며 Nomad Pocket JSON export를 읽는다.
- Finance Agent는 소비 확인, 소비 패턴 분석, 예산 압력 감지, 조정 제안을 담당한다.
- 가계부 원본 앱의 데이터 수정, 삭제, 카테고리 write-back은 사용자 승인 전에는 하지 않는다.

### English Transcript Folder

다른 AI와 영어 학습한 녹취/텍스트가 iCloud에 저장된다면, 해당 폴더를 read-only input으로 삼을 수 있다.

초기에는 transcript 원문 전체를 영구 저장하지 않고 metadata, 분량, 주제, 학습 후보만 정규화한다.

### Social

Social agent는 후순위다. API 안정성, 계정 권한, platform policy가 복잡하므로 우선 raw export나 수동 기록을 전제로 둔다.

자동 게시 또는 계정 수정은 초기 범위에 포함하지 않는다.
