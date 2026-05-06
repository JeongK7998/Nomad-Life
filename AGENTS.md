# AGENTS.md

## Project Name

Nomad Life Agent on Hermes

## Project Definition

Nomad Life Agent는 Hermes Agent를 기반으로 한 개인 노마드 라이프 운영 에이전트 하네스다.

이 프로젝트의 목표는 단순한 웹앱, 기록 앱, 챗봇을 만드는 것이 아니다. 사용자의 노마드 생활 데이터를 수집하고, 각 영역별 에이전트가 분석하며, 총괄 에이전트가 이를 조율해 하루 운영안, 주간 전략, 생활 리스크, 실행 제안, 시각화 데이터를 생성하는 개인 AI 운영 시스템을 만드는 것이다.

Agents 시스템은 가장 중요한 요소이며 openclaw, Hermes Agent 등을 활용할 예정이지만 우선은 Hermes Agent를 활용할 예정이다. Hermes Agent는 이 프로젝트의 중심 런타임이다. Nomad Dashboard는 에이전트 자체가 아니라 사용자가 모든 기기에서 입력, 확인, 승인, 시각화를 수행하는 사용자 인터페이스다.

이 시스템은 단계별로 개발할 예정이며 실사용과 함께 중요한 Value를 발굴하며 업데이트를 할 예정이고 오랜 개발을 통해 중간중간 발전하는 AI 기능도 업데이트 할 예정이다. 따라서 가장 중요한 것은 지속적으로 발전 및 유지보수가 가능한 구조로 개발하는것으로 하드 코딩 을 지양하고 단편적인 요구사항의 구현에만 집중하지 않도록 한다.

또한, 여러 요소들이 중간에 업데이트 될 수 있으므로 AGENTS.md는 항상 최신으로 유지한다. AGENTS.md를 업데이트할 때 원칙이 위배되거나 충돌하는 내용은 항상 경고하고, 일관된 원칙을 고수할 수 있도록 한다.

---

## AGENTS.md Governance

AGENTS.md는 이 프로젝트의 운영 헌법이다. 에이전트, 런타임, 데이터 구조, 권한, 웹앱 방향성, 자동화 정책이 변경될 때는 AGENTS.md도 함께 최신 상태로 유지한다.

### Modification Authority

Codex는 AGENTS.md를 수정할 수 있다.

단, 다음에 해당하는 변경은 반드시 사용자에게 먼저 확인하고 승인받은 뒤 반영한다.

- Hermes Agent Runtime 중심 원칙을 약화시키는 변경
- 웹앱을 에이전트의 중심 런타임으로 바꾸는 변경
- Coordinator Agent의 단일 소통 창구 원칙을 깨는 변경
- 사용자 승인 없이 민감한 데이터나 외부 앱을 수정하도록 권한을 넓히는 변경
- 초기 MVP 범위를 지나치게 확장해 유지보수 가능성을 해치는 변경
- 로컬 우선, 프라이버시 우선, 로그 기반 실행 원칙과 충돌하는 변경
- 사용자를 통제하거나 모든 목표를 강제하는 방향의 변경

오타 수정, 구조 정리, 합의된 내용을 명확히 문서화하는 변경은 바로 반영할 수 있다.

### Review Rhythm

프로젝트가 발전하면서 사용자와 Codex는 AGENTS.md를 주기적으로 리뷰한다.

리뷰 목적:

- 현재 구현 방향이 Core Philosophy와 맞는지 확인
- 새로 발견한 Value를 문서에 반영
- MVP 범위가 과도하게 커지지 않았는지 점검
- 새로운 런타임, 도구, MCP, 외부 연동이 기존 권한 원칙과 충돌하지 않는지 검토
- 실제 사용 경험을 바탕으로 Skill 구조와 데이터 모델을 업데이트

---

## Core Concept

```txt
Hermes Agent Runtime
├─ AGENTS.md
├─ Nomad Skills
├─ Tools / MCP
├─ Cron Jobs
├─ Memory
├─ Local Data Folder
└─ Web / Mobile Interface
```

핵심 구조는 다음과 같다.

```txt
iPhone / iPad / Web Quick Capture
        ↓
Hermes Runtime
        ↓
Nomad Skills
        ↓
Coordinator Agent
        ↓
Reports / Dashboard JSON / Action Suggestions
        ↓
Nomad Dashboard / Quick Panels
```

---

## Core Philosophy

- 앱이 중심이 아니라 Hermes Agent Runtime이 중심이다.
- Nomad Dashboard는 입력, 확인, 시각화, 승인 UI 역할을 한다.
- Dashboard는 Mac, iPad, iPhone에서 접근 가능해야 한다.
- Quick Panels는 Dashboard와 같은 제품 표면에 속하지만 빠른 입력에 특화된 모바일 우선 화면이다.
- 사용자는 여러 에이전트와 직접 대화하지 않는다.
- Coordinator Agent가 사용자와의 소통을 일원화한다.
- 각 에이전트는 독립된 역할을 갖지만 최종 판단은 Coordinator가 조율한다.
- 모든 목표를 균등하게 강제하지 않는다.
- 상황에 따라 집중할 영역과 내려놓을 영역을 제안한다.
- 자동 수집 가능한 데이터는 자동화한다.
- 사용자가 직접 분류하지 않도록 Quick Capture가 입력을 해석한다.
- 기록보다 해석, 조율, 실행 제안이 중요하다.
- 실행 권한은 단계적으로 부여한다.
- 초기에는 read-only와 draft 중심으로 운영한다.
- 자동 실행은 안전한 반복 작업부터 시작한다.
- 모든 실행은 로그로 남긴다.
- 시각화는 핵심 기능이다.
- 개인적이고 민감한 데이터는 local-first로 다룬다.
- 클라우드와 VPS는 availability를 보완하는 얇은 계층으로 시작한다.

---

## Product Design System

Nomad Life의 웹/모바일 인터페이스는 `Design System/`에 보관된 Wanted Design System을 참고하되, Wanted 브랜드를 복제하지 않고 Nomad Life의 운영 cockpit 경험에 맞게 내재화한다.

핵심 원칙:

- Wanted-inspired, Nomad-owned.
- Korean-first UI를 기본으로 한다.
- 화려한 마케팅 UI가 아니라 조용하고 밀도 있는 생활 운영 cockpit을 만든다.
- Pretendard를 기본 폰트로 사용한다.
- 색상, spacing, radius, shadow는 semantic token을 우선 사용한다.
- 4pt grid를 따른다.
- primary blue는 주요 CTA, 활성 상태, 핵심 신호에만 제한적으로 사용한다.
- 카드와 패널은 선 중심의 flat UI를 기본으로 하고 shadow는 popover, modal, floating layer에만 제한적으로 사용한다.
- Wanted 로고, Wanted 전용 브랜드 자산, 채용 제품 전용 카피 패턴은 Nomad Life UI에 직접 사용하지 않는다.
- 디자인 시스템 변경은 `docs/DESIGN_SYSTEM.md`와 web token 파일에 함께 반영한다.

---

## Target User

3개월 이상 해외 또는 국내 여러 지역에서 노마드 생활을 하는 사용자.

주요 관심사는 다음과 같다.

1. AI 작업 및 바이브 코딩
2. 콘텐츠 크리에이팅 및 소셜 활동
3. 여행 및 체험
4. 운동, 수영, 서핑 등 건강 관리
5. 식단 관리
6. 금전 관리
7. 영어 공부
8. 휴식과 회복

---

## Hermes-Based Architecture

### 1. Hermes Runtime

Hermes는 이 프로젝트의 실행 중심이다.

Hermes의 역할:

- 프로젝트 지침인 AGENTS.md 읽기
- Nomad Skills 실행
- 로컬 파일 읽기/쓰기
- 캘린더, 시트, 메모, 파일, 브라우저 등 외부 도구 연결
- Cron 기반 반복 작업 실행
- 보고서 생성
- dashboard.json 생성
- 사용자 승인 기반 액션 수행
- 장기적으로 MCP를 통해 외부 앱과 연결

현재 Hermes 연결 상태:

- 로컬 Hermes 실행 파일은 `/Users/jongiljeong/.local/bin/hermes`다.
- Hermes는 이 프로젝트 root에서 AGENTS.md를 읽을 수 있다.
- 초기 연결은 `scripts/run_nomad_daily.py` 같은 deterministic runner를 Hermes가 호출하거나 검토하는 방식으로 시작한다.
- Hermes가 직접 파일을 수정하는 단계는 output contract가 안정된 뒤 확장한다.
- Calendar, Notes, Reminders 같은 macOS 앱 전용 MCP는 아직 설정되어 있지 않다.
- macOS 앱 데이터는 프로젝트 소유 read-only bridge script를 통해 `data/context/*.json`으로 정규화한 뒤 Hermes가 읽는다.
- 초기 샘플 local app context agent는 `nomad-calendar-context`와 `nomad-notes-context`다.
- local app context agent는 원본 앱을 수정하지 않으며, 모든 조회는 action log에 남긴다.

### 2. Nomad Dashboard

Nomad Dashboard는 사용자가 보는 인터페이스다.

역할:

- Quick Capture 입력
- Today Dashboard 표시
- Agent Council 표시
- Coordinator Brief 표시
- Life Dashboard 시각화
- Weekly Review 표시
- 실행 승인 버튼 제공
- 데이터 수정 UI 제공

Nomad Dashboard는 초기에는 AI를 직접 호출하지 않는다. Hermes가 생성한 `dashboard/*.json`, `reports/*.md`, 또는 Supabase `dashboard_snapshots`를 읽어 보여주는 구조를 우선한다.

배포 원칙:

- Local Dashboard는 Mac 개발과 Hermes 검증을 위한 모드다.
- Hosted Dashboard는 Vercel에 배포해 Mac, iPad, iPhone에서 접근 가능한 모드다.
- Hosted Dashboard는 Supabase snapshot과 queue를 읽고 쓴다.
- Hosted Dashboard가 Hermes Runtime을 대체하지 않는다.

### 2-1. Quick Panels

Quick Panels는 iPhone/iPad/Mac에서 빠르게 입력하기 위한 전용 화면이다.

초기 Quick Panels:

- Workout Quick
- Capture Quick
- Meal Quick

Finance 전용 지출 입력 Quick Panel은 만들지 않는다. 지출 입력은 사용자의 기존 가계부 앱에서 계속 수행하며, Nomad Life Finance Agent는 해당 앱의 export 또는 read-only 데이터를 주기적으로 가져와 분석한다.

원칙:

- 선택지는 가능한 드롭다운과 안정적인 ID를 사용한다.
- 텍스트 자유 입력은 메모와 raw capture에 한정한다.
- 기본 저장 경로는 Supabase queue다.
- Mac local server가 켜져 있을 때는 local API mode도 사용할 수 있다.
- iCloud Drive는 primary가 아니라 fallback/dropbox로 유지한다.

### 3. iPhone / iPad Input Layer

iPhone과 iPad는 가장 중요한 입력 도구다.

입력 방식:

- 빠른 텍스트 입력
- 음성 입력
- 식사 사진 업로드
- 영수증 사진 업로드
- 장소 메모
- 운동 완료 체크
- 하루 체크인
- 홈 화면 바로가기
- iOS 단축어 연동
- Telegram 명시적 capture 입력
- 추후 액션 버튼 또는 뒷면 탭 연동 가능성 고려

### 4. Local Data Folder

Hermes가 읽고 쓸 수 있는 데이터 폴더를 표준화한다.

```txt
nomad-life-agent/
  AGENTS.md
  data/
    inbox/
      local/
      cloud/
    sync/
      pending/
      processed/
    captures/
    expenses/
    meals/
    health/
    work/
    travel/
    content/
    english/
    rest/
    context/
    action_logs/
  reports/
    daily/
    weekly/
    monthly/
  dashboard/
    today.json
    weekly.json
    life-balance.json
  skills/
  scripts/
```

### 5. Physical Runtime Strategy

Nomad Life Agent는 사용자가 이동 중이고 MacBook이 항상 켜져 있지 않을 수 있다는 현실을 전제로 설계한다.

기본 원칙:

- MacBook은 private context worker다.
- Supabase, Vercel 같은 웹서비스는 availability를 보완하는 cloud-light layer다.
- Codex가 Supabase를 언급할 때는 혼동 방지를 위해 항상 대상 Supabase 프로젝트명을 함께 명시한다.
- Supabase 프로젝트명이 아직 확정 또는 문서화되지 않은 상태에서는 `Supabase 프로젝트명 미확인`이라고 표시하고 사용자에게 정확한 프로젝트명을 확인한다.
- 현재 Nomad Life cloud-light 대상 Supabase 프로젝트는 `Nomad Life`이며 URL은 `https://ikeubpdajcuqlvbvvhbq.supabase.co`다.
- 초기 MVP는 MacBook local-first로 시작한다.
- Cloud/VPS는 처음부터 모든 개인 데이터를 처리하지 않는다.
- Cloud-light layer는 우선 Quick Panel queue, dashboard snapshot, auth, deployment처럼 얇은 역할만 담당한다.
- 캘린더, 메모, 사진, 작업 로그, 로컬 파일처럼 개인 맥 환경 접근이 필요한 작업은 Local Hermes가 담당한다.
- 민감한 데이터 수정, 외부 앱 변경, 캘린더/메모/금융/건강 관련 실행은 사용자 승인 없이 수행하지 않는다.

권장 흐름:

```txt
iPhone / iPad / Mac Dashboard + Quick Panels
        ↓
Vercel-hosted Nomad Dashboard
        ↓
Supabase queue / dashboard snapshots
        ↓
Mac Hermes Worker
        ↓
Local Data + Personal Apps
        ↓
Reports / Dashboard JSON
        ↓
Supabase dashboard snapshots
        ↓
Nomad Dashboard on Mac / iPad / iPhone
```

초기 단계에서는 다음 순서를 따른다.

1. Mac-only local runtime으로 가치 검증
2. GitHub 저장소와 Vercel 배포 경로 정리
3. Supabase queue/snapshot/auth 도입
4. Mac Hermes Worker가 Supabase queue를 처리하고 snapshot을 publish
5. 충분히 검증된 뒤 cloud cron, external integration 확장

Cloud-light 도입 시에도 local-first/privacy-first 원칙을 유지한다. Supabase는 항상 켜져 있는 접수창과 표시 계층으로 시작하며, 개인 데이터 해석과 승인 기반 실행은 Local Hermes 중심으로 유지한다.

현재 mobile capture 결정:

- 기본 mobile capture와 Quick Panel 입력은 Supabase queue를 사용한다.
- iCloud Drive inbox는 primary가 아니라 fallback, offline dropbox, 사진/영수증/export 파일 전달용으로 유지한다.
- Local Dashboard는 MacBook이 켜져 있을 때 즉시 입력과 즉시 dashboard 갱신을 담당한다.
- Hosted Dashboard는 Supabase dashboard snapshot을 읽어 모든 기기에서 확인 가능해야 한다.
- Telegram은 기본적으로 Conversation Channel이지만, `캡쳐:`, `기록:`, `저장:`, `capture:`처럼 명시된 일반 텍스트 입력은 Quick Capture로 저장할 수 있다.
- Telegram `/capture` 같은 slash command는 Hermes gateway 명령어와 충돌하므로 사용하지 않는다.
- Telegram 일반 대화는 자동으로 저장하지 않는다. 저장 의도가 불명확하면 Coordinator가 확인하거나 저장 제안만 한다.
- Quick Capture 저장 후에는 dashboard, notification candidates 같은 파생 로컬 출력이 함께 갱신된다. Finance 분석은 별도 외부 가계부 export/read-only import를 기준으로 갱신한다.
- 지출 기록은 처음부터 확정 가계부로 저장하지 않고 `data/expenses/expense-candidates.json`에 review candidate로 생성한다.

현재 개발 초점:

- 세부 도메인 기능을 깊게 구현하기보다 큰 시스템 블록의 책임과 경계를 먼저 확정한다.
- Input, Data Contract, Hermes Runtime, Local Context, Skill Council, Dashboard, Quick Panels, Communication 블록은 얇은 MVP 범위로 검증한다.
- Automation과 Cloud-Light 블록은 수동 검증이 안정된 뒤 확장한다.
- 지출 확정, 식사 리뷰, 액션 승인 UI, 알림 전송 같은 상세 워크플로우는 범위 합의 후 구현한다.
- 최종적으로 가장 중요한 산출물은 Dashboard다. Dashboard는 하위 에이전트 역할이 명확해진 뒤 각 영역의 비중, 누적량, 리스크, 조율안을 보여준다.
- 현재 샘플 하위 에이전트는 Health, English, Calendar/Schedule Context를 우선 검증한다.
- Finance는 사용자의 기존 가계부 입력 흐름을 대체하지 않고, 향후 Supabase 또는 export 기반 read-only 분석자로 설계한다.
- Social/Creator와 AI Work 에이전트는 역할이 더 명확해질 때까지 후순위로 둔다.
- 시간 관련 Dashboard는 명확한 capture 표현에서 activity allocation 후보를 만들고, 사용자가 어떤 활동에 시간을 쓰고 있는지 영역별 비중과 누적량을 보여주는 방향으로 시작한다.
- Activity Dashboard는 하루 24시간 대비 비중, 이번 달 경과일 기준 월간 비중, 영역별 누적 시간을 함께 보여준다.

### 6. Communication Layer

Nomad Life의 사용자 접점은 역할별로 분리한다.

```txt
Capture Channel
  Shortcuts / Web Quick Capture / Telegram explicit capture / local inbox
  -> 빠른 데이터 입력

Dashboard Channel
  Nomad Dashboard on Vercel / Local Dashboard on Mac
  -> dashboard, reports, action center, logs 확인

Quick Panel Channel
  Workout Quick / Capture Quick / Meal Quick
  -> 빠른 구조화 입력

Conversation Channel
  Hermes Chat / Telegram
  -> Coordinator와 질문, 계획, 회고, 논의

Notification Channel
  Hermes Telegram notification
  -> brief, risk, opportunity, approval-needed alert
```

사용자는 여러 하위 에이전트와 직접 대화하지 않는다. 채팅에서도 Coordinator Agent가 단일 창구가 되며, Calendar, Notes, Work, Rest, Travel 등 하위 Skill은 Coordinator가 내부적으로 참조한다.

Telegram은 장기적으로 기본 conversation/notification 채널이 될 수 있다. 단, Telegram은 데이터 저장소가 아니며 중요한 기록은 Quick Capture 또는 명시적 capture 전환을 통해 저장한다.

초기 테스트는 `scripts/run_hermes_coordinator_chat.py`로 수행한다.

Conversation은 read-only context 조회, 분석, 제안, 초안 생성을 할 수 있다. Calendar, Notes, Reminders, 외부 앱 수정이나 메시지 전송은 사용자 승인 전에는 수행하지 않는다.

---

## Agent Authority Levels

에이전트 권한은 단계적으로 확장한다.

### Level 1. Read

에이전트는 데이터를 읽고 분석만 한다.

가능한 작업:

- 캘린더 읽기
- 가계부 CSV 읽기
- 사진 폴더 읽기
- 운동 export 읽기
- 메모 읽기
- 작업 로그 읽기

### Level 2. Draft

에이전트는 실행 초안을 만든다.

가능한 작업:

- 일정 초안 생성
- 콘텐츠 초안 생성
- 가계부 분류 제안
- 여행 체크리스트 생성
- 영어 복습 카드 생성
- 운동 계획 제안

### Level 3. Approve-to-Act

사용자 승인 후 실행한다.

가능한 작업:

- 캘린더 일정 추가
- 리마인더 생성
- 메모 저장
- 보고서 저장
- 콘텐츠 초안 파일 생성
- dashboard.json 업데이트

### Level 4. Auto Action

안전한 반복 작업만 자동 실행한다.

가능한 작업:

- daily brief 생성
- weekly review 생성
- dashboard.json 업데이트
- 데이터 백업
- 정해진 폴더 정리
- 실행 로그 기록

초기 버전에서는 Level 1과 Level 2 중심으로 개발한다. Level 3은 명확한 버튼 승인 후 실행한다. Level 4는 충분히 검증된 반복 작업에만 적용한다.

---

## Nomad Skills

Hermes 기반에서는 각 에이전트를 Skill 단위로 정의한다.

필요한 Skill 목록:

```txt
nomad-coordinator
nomad-quick-capture
nomad-calendar-context
nomad-notes-context
nomad-finance
nomad-food
nomad-health
nomad-work
nomad-travel-guide
nomad-creator
nomad-english
nomad-rest
nomad-weekly-review
nomad-dashboard-export
```

각 Skill은 다음 구조를 가져야 한다.

```txt
목적
입력 데이터
읽을 파일 위치
사용 가능한 도구
수행 절차
출력 형식
금지 사항
예시
```

---

# Core Agents / Skills

## 1. nomad-coordinator

### Role

전체 시스템의 총괄 에이전트다.

사용자와의 소통을 일원화하고, 각 Skill의 분석 결과를 종합해 최종 조율안을 제공한다.

### Input Data

- 사용자 Quick Capture 입력
- 각 에이전트 분석 결과
- 오늘 일정
- 최근 지출 상태
- 최근 식단 상태
- 최근 운동/건강 상태
- 최근 작업 상태
- 최근 휴식 상태
- 여행 일정
- 콘텐츠 후보
- 영어 학습 상태

### Responsibilities

- 사용자 입력을 각 영역으로 분류
- 각 Skill의 판단 종합
- 오늘의 우선순위 제안
- 내려놓아도 되는 영역 제안
- 주의할 리스크 도출
- 내일 또는 이번 주 행동 제안
- Agent Council 생성
- Coordinator Brief 생성
- 시각화 데이터 생성 요청
- 주간 회고 생성 요청
- 실행 권한이 필요한 경우 승인 요청 생성

### Output Files

```txt
reports/daily/YYYY-MM-DD-brief.md
dashboard/today.json
dashboard/life-balance.json
```

---

## 2. nomad-quick-capture

### Role

모든 입력의 입구 역할을 한다.

사용자가 입력한 텍스트, 음성, 사진, 금액, 메모를 받아 자동으로 의미를 분류하고 관련 Skill에 연결한다.

### Input Data

- 텍스트 메모
- 음성 변환 텍스트
- 사진
- 지출 금액
- 장소명
- 감정/컨디션
- 하루 요약
- 식사 사진
- 영수증 사진

### Collection Methods

- Web Quick Capture
- iPhone Shortcut
- iPad Shortcut
- Telegram 또는 Slack 메시지
- 파일 업로드
- 폴더 저장

### Responsibilities

- 원본 입력 저장
- 입력 내용 자동 분류
- 관련 Skill 태깅
- 불확실한 정보 표시
- 필요한 후속 질문 생성
- parsed capture JSON 생성

### Output Files

```txt
data/captures/YYYY-MM-DD.jsonl
data/context/latest-captures.json
```

---

## 3. nomad-calendar-context

### Role

Apple Calendar를 read-only로 조회해 오늘과 근미래의 일정 맥락을 제공하는 local app context Skill이다.

이 Skill은 사용자의 하루를 직접 결정하지 않는다. 일정 밀도, 이동 가능성, 회복 여지, 시간 압박 신호를 Coordinator, Rest, Travel Guide Agent가 참고할 수 있도록 정규화한다.

### Input Data

- 오늘과 내일의 Calendar event
- 일정 제목
- 시작/종료 시간
- 캘린더 이름
- 장소
- 종일 일정 여부

### Collection Methods

- `scripts/read_calendar_context.py`
- Swift EventKit bridge
- `scripts/run_nomad_daily.py --include-local-apps`
- Local Dashboard Context refresh

### Responsibilities

- Calendar 접근 가능 여부 확인
- 일정 수와 시간 밀도 요약
- 이동/예약/작업/소셜/회복 신호 추정
- 일정 기반 리스크 후보 생성
- Coordinator에게 schedule context 제공
- 원본 Calendar 앱 수정 금지

### Output Files

```txt
data/context/calendar-context.json
```

---

## 4. nomad-notes-context

### Role

Apple Notes를 제한된 범위에서 read-only로 조회해 메모 기반 맥락 후보를 제공하는 local app context Skill이다.

초기에는 전체 Notes를 읽지 않고 `Nomad Life` 같은 전용 폴더만 조회한다.

### Input Data

- Note 제목
- 생성일
- 수정일
- 폴더명
- 계정명
- 선택적 짧은 본문 preview

### Collection Methods

- `scripts/read_notes_context.py --folder "Nomad Life"`
- AppleScript bridge
- `scripts/run_nomad_daily.py --include-local-apps`
- Local Dashboard Context refresh

### Responsibilities

- Notes 접근 가능 여부 확인
- 지정 폴더 내 note metadata 조회
- note를 context candidate로 분류
- Work, Creator, Travel, Rest, Quick Capture와 연결될 가능성 표시
- Coordinator에게 note context 제공
- 원본 Notes 앱 수정 금지

### Output Files

```txt
data/context/notes-context.json
```

---

## 5. nomad-finance

### Role

금전 관리 Skill이다.

기존 개인 가계부와 연계하여 노마드 생활의 예산 소진 속도와 과소비 원인을 분석한다.

### Input Data

- 날짜
- 금액
- 통화
- 환율
- 카테고리
- 결제수단
- 장소
- 만족도
- 필수/선택 여부
- 기존 가계부 CSV
- Google Sheets 데이터
- Supabase 기반 개인 가계부 read-only view 또는 export
- 영수증 사진 OCR 결과

### Collection Methods

- 기존 가계부 CSV import
- Google Sheets 연동
- Supabase read-only API 또는 자동 export
- 다른 가계부 앱의 주기적 export/download
- 영수증 사진 OCR 결과는 향후 보조 입력 후보로만 검토

### Responsibilities

- 예산 소진 속도 계산
- 카테고리별 지출 분석
- 식비/카페/교통/체험비 분리
- 남은 체류 기간 기준 예상 지출 계산
- 과소비 원인 도출
- 가치 소비와 낭비성 소비 구분 보조
- Food, Travel, Work Agent와 지출 데이터 연결
- Budget Burn Rate 시각화 데이터 생성

초기 원칙:

- Finance Agent는 개인 가계부 입력 앱을 대체하지 않는다.
- 사용자는 기존 개인 앱에서 지출을 입력한다.
- Nomad Life는 다른 앱의 지출 내역을 주기적으로 download/export 또는 read-only 방식으로 가져와 현황, 추세, 리스크를 분석한다.
- Finance Agent는 지출 기록 입력 UI가 아니라 분석자와 조언자 역할을 한다.
- Supabase credential, API key, schema 접근은 별도 승인 후 진행한다.

### Output Files

```txt
data/expenses/normalized-expenses.json
reports/daily/YYYY-MM-DD-finance.md
dashboard/budget.json
```

---

## 6. nomad-food

### Role

식단 관리 Skill이다.

관광지에서 매일 맛있는 음식을 먹는 방식이 아니라, 즐기는 식사와 관리식의 균형을 조율한다.

### Input Data

- 식사 사진
- 식사 시간
- 식사 장소
- 메뉴
- 식사 비용
- 만족도
- 포만감
- 음주 여부
- 관리식/즐기는 식사 여부
- 단백질/채소/탄수화물 추정
- Finance Agent의 식비 데이터

### Collection Methods

- 식사 사진 업로드
- 빠른 음성 메모
- 지출 데이터 연동
- 영수증 사진
- 수동 만족도 입력
- Vision 분석

### Responsibilities

- 식사 패턴 분석
- 관리식과 즐기는 식사 비율 계산
- 단백질/채소 부족 가능성 추정
- 외식 빈도 분석
- 식비와 식단 균형 연결
- 운동/휴식 데이터와 연동한 식사 제안
- Meal Balance 시각화 데이터 생성

### Output Files

```txt
data/meals/normalized-meals.json
reports/daily/YYYY-MM-DD-food.md
dashboard/meal-balance.json
```

---

## 7. nomad-work

### Role

디지털 노마드 작업과 AI 작업을 관리한다.

### Input Data

- 작업 프로젝트
- 작업 시간
- 사용 도구
- 작업 장소
- 산출물
- 막힌 점
- 다음 액션
- 집중도
- Git log
- Codex / Claude Code 작업 메모
- 캘린더 작업 블록

### Collection Methods

- 하루 체크인
- 작업 종료 후 짧은 입력
- 작업 폴더 로그
- Git commit log
- Codex CLI 로그
- Claude Code CLI 로그
- 캘린더 작업 블록

### Responsibilities

- 작업 흐름 요약
- 다음 작업 단위 제안
- 막힌 지점 정리
- 프로젝트별 진척도 추정
- 작업 장소와 생산성 연결
- 과작업 여부 감지
- Creator Agent와 콘텐츠화 가능성 연결
- Rest Agent와 피로도 조율

### Output Files

```txt
data/work/work-sessions.json
reports/daily/YYYY-MM-DD-work.md
dashboard/work.json
```

---

## 8. nomad-health

### Role

운동과 건강 상태를 관리한다.

### Input Data

- 운동 종류
- 운동 시간
- 운동 강도
- 근력운동 세부 기록
- 운동 부위
- 운동명
- 세트 수
- 무게
- 반복 수
- RPE 또는 체감 난이도
- 걸음 수
- 수면 시간
- 심박
- 컨디션
- 피로도
- 통증 여부
- 수영/서핑/헬스/산책 기록
- Apple Health export
- 운동 앱 export

### Collection Methods

- 수동 운동 체크
- Web/Cockpit workout detail form
- iPhone 홈 화면 또는 Shortcut 기반 workout form 진입
- Apple Health export
- 운동 앱 export
- Apple Watch 데이터
- 하루 체크인
- 캘린더 연동
- 추후 HealthKit 연동

현재 Health Agent 방향:

- 운동 앱 또는 Apple Health / HealthKit 연동은 read-only workout import로 시작한다.
- HealthKit 접근은 민감 데이터이므로 별도 승인 전에는 구현하거나 실행하지 않는다.
- 근력운동 디테일은 별도 workout form에서 빠르게 수동 입력한다.
- Quick Capture의 `근력운동 시작`, `운동 기록` 같은 입력은 workout form 진입 트리거 또는 workout session 후보로 해석할 수 있다.
- 구조화된 workout session은 capture와 분리해 저장하되, 요약 capture도 함께 남겨 audit trail을 유지한다.

### Responsibilities

- 운동 부족 감지
- 과운동 감지
- 회복 필요성 판단
- 수영/서핑/헬스 균형 관리
- 근력운동 빈도 분석
- 부위별 운동 인터벌 분석
- 운동별 무게/반복/세트 변화 추적
- 점진적 과부하 또는 정체 후보 감지
- 컨디션 기반 운동 강도 조정
- 일정과 연동한 운동 제안
- Rest Agent와 회복 상태 조율

### Output Files

```txt
data/health/health-summary.json
data/health/workout-sessions.jsonl
reports/daily/YYYY-MM-DD-health.md
dashboard/health.json
```

---

## 9. nomad-travel-guide

### Role

여행과 체험을 관리하는 가이드 Skill이다.

특정 지역에 한정하지 않고, 노마드 생활 중 이동, 체험, 관광, 예약, 준비물을 조율한다.

### Input Data

- 일정
- 예약 정보
- 지역
- 이동 계획
- 숙소 정보
- 날씨
- 체험 후보
- 예산
- 피로도
- 여행 문서
- 비자/보험 관련 메모

### Collection Methods

- 캘린더 연동
- 예약 메일 또는 문서
- 수동 여행 계획 입력
- 날씨 API
- 위치/장소 기록
- 체크리스트
- Maps / Places 데이터

### Responsibilities

- 이동 일정 확인
- 체험 추천
- 여행 리스크 감지
- 장거리 일정과 피로도 조율
- 예산과 여행 활동 균형 분석
- 준비물 체크
- 여행 경험을 콘텐츠 소재로 연결
- 영어 상황 미션과 연결

### Output Files

```txt
data/travel/travel-context.json
reports/daily/YYYY-MM-DD-travel.md
dashboard/travel.json
```

---

## 10. nomad-creator

### Role

콘텐츠 크리에이팅과 소셜 활동을 관리한다.

### Input Data

- 사진
- 영상
- 하루 경험
- 메모
- 만난 사람
- 대화 주제
- 작성한 글
- 게시 여부
- 반응 지표
- 콘텐츠 아이디어
- 여행 경험
- AI 작업 로그

### Collection Methods

- 사진 업로드
- 음성 메모
- daily check-in
- 작성 파일 읽기
- SNS 지표 수동 입력
- 콘텐츠 초안 저장
- 여행/장소 데이터 연동

### Responsibilities

- 콘텐츠 소재 추출
- 블로그/스레드/인스타 소재 분리
- 시리즈화 가능한 주제 제안
- 소셜 활동 기록
- 경험을 콘텐츠 자산으로 변환
- 콘텐츠 초안 생성
- 콘텐츠 생산 부담과 휴식 상태 조율

### Output Files

```txt
data/content/content-ideas.json
reports/daily/YYYY-MM-DD-creator.md
dashboard/content.json
```

---

## 11. nomad-english

### Role

노마드 생활에서 실제로 필요한 영어 학습을 관리한다.

### Input Data

- 오늘의 상황
- 내일 일정
- 말하지 못한 표현
- 새로 배운 표현
- 대화 메모
- 음성 메모
- 복습 여부
- 자신감 점수
- 여행/소셜/운동 일정

### Collection Methods

- 음성 입력
- 하루 체크인
- 상황별 메모
- GPT Voice 연습 요약
- 캘린더/여행 일정 기반 상황 추정

### Responsibilities

- 내일 쓸 표현 추천
- 실제 상황 기반 미니 롤플레이 생성
- 자주 막히는 표현 정리
- 복습 카드 생성
- 피로도에 따른 학습량 조절
- 여행/소셜 일정과 연동한 영어 미션 생성

### Output Files

```txt
data/english/english-notes.json
reports/daily/YYYY-MM-DD-english.md
dashboard/english.json
```

---

## 12. nomad-rest

### Role

휴식과 회복을 관리한다.

### Input Data

- 수면 시간
- 수면 만족도
- 피로도
- 감정 상태
- 일정 밀도
- 작업 시간
- 운동 강도
- 소셜 활동량
- 혼자 있고 싶은 정도
- 디지털 작업 시간

### Collection Methods

- 하루 체크인
- Health data
- 캘린더 분석
- 작업 로그
- 감정 선택 폼
- 음성 메모

### Responsibilities

- 번아웃 위험 감지
- 일정 과밀 판단
- 회복 우선일 제안
- 밤 작업 제한 제안
- 운동 강도 조율
- 소셜 활동 과부하 감지
- 다른 Agent의 과도한 제안을 완화

### Output Files

```txt
data/rest/rest-status.json
reports/daily/YYYY-MM-DD-rest.md
dashboard/rest.json
```

---

## 13. nomad-weekly-review

### Role

한 주의 생활 패턴을 종합하고 다음 주 전략을 제안한다.

### Input Data

- daily briefs
- agent reports
- expenses
- meals
- health summary
- work sessions
- travel context
- content ideas
- english notes
- rest status

### Responsibilities

- 주간 핵심 패턴 도출
- 집중했던 영역 분석
- 내려놓았던 영역 분석
- 예산/식단/운동/휴식 리스크 정리
- 다음 주 전략 제안
- 콘텐츠 후보 정리
- Life Balance 시각화 업데이트

### Output Files

```txt
reports/weekly/YYYY-WW-review.md
dashboard/weekly.json
dashboard/life-balance.json
```

---

## 14. nomad-dashboard-export

### Role

각 Agent의 분석 결과를 웹앱이 읽을 수 있는 JSON으로 변환한다.

### Responsibilities

- reports 데이터를 dashboard JSON으로 변환
- chart data 생성
- Agent Council 데이터 생성
- Today Dashboard 데이터 생성
- Weekly Review 데이터 생성
- Action Suggestions 생성

### Output Files

```txt
dashboard/today.json
dashboard/weekly.json
dashboard/budget.json
dashboard/meal-balance.json
dashboard/life-balance.json
dashboard/actions.json
```

---

# Data Model

## 1. captures

```txt
id
created_at
date
type: text | voice | photo | expense | checkin
raw_content
media_url
parsed_result
linked_agents
confidence
status
```

## 2. expenses

```txt
id
date
amount
currency
exchange_rate
category
subcategory
place
payment_method
satisfaction
required_or_optional
note
source
```

## 3. meals

```txt
id
date
time
photo_url
meal_type
place
cost
satisfaction
fullness
estimated_balance
protein_estimate
vegetable_estimate
carb_estimate
alcohol
note
source
```

## 4. work_sessions

```txt
id
date
project
start_time
end_time
place
tool
output
blocker
next_action
focus_score
source
```

## 5. activities

```txt
id
date
type
duration
intensity
steps
calories
heart_rate
source
note
```

## 6. places

```txt
id
name
area
type
wifi_score
noise_score
cost_level
work_friendly_score
satisfaction
visit_count
note
```

## 7. content_ideas

```txt
id
date
source
topic
format
status
draft
related_photo
related_place
note
```

## 8. english_notes

```txt
id
date
situation
expression
difficulty
review_status
source
note
```

## 9. agent_reports

```txt
id
date
agent_name
status
score
insight
recommendation
risk
data_sources
confidence
```

## 10. daily_briefs

```txt
id
date
summary
focus_today
let_go_today
risks
recommendations
missions
visualization_data
```

## 11. weekly_reviews

```txt
id
week_start
week_end
summary
focus_distribution
life_balance_scores
budget_status
health_status
content_opportunities
next_week_strategy
```

## 12. action_logs

모든 실행 기록 저장소.

```txt
id
created_at
agent_name
action_type
target_tool
reason
input
output
status
approval_required
approved_by_user
error
```

---

# Cron Jobs

Hermes Cron을 활용해 반복 작업을 자동화한다.

## Morning Brief

```txt
Schedule: every day at 08:00
Skill: nomad-coordinator
Output:
- reports/daily/YYYY-MM-DD-brief.md
- dashboard/today.json
```

역할:

- 오늘 일정 확인
- 최근 지출 상태 확인
- 최근 식단 상태 확인
- 최근 운동/휴식 상태 확인
- 오늘 집중할 것 3개 생성
- 내려놓아도 되는 것 제안
- 리스크 생성

## Evening Capture Review

```txt
Schedule: every day at 22:00
Skill: nomad-quick-capture + nomad-coordinator
Output:
- data/context/YYYY-MM-DD-context.json
- reports/daily/YYYY-MM-DD-review.md
```

역할:

- 오늘 입력된 capture 정리
- 각 영역으로 분류
- Daily context 생성
- 내일 반영할 요약 생성

## Weekly Strategy Review

```txt
Schedule: every Sunday at 20:00
Skill: nomad-weekly-review
Output:
- reports/weekly/YYYY-WW-review.md
- dashboard/weekly.json
```

역할:

- 주간 패턴 분석
- 집중/부족 영역 도출
- 예산/식단/운동/휴식 상태 정리
- 다음 주 전략 제안

## Budget Watch

```txt
Schedule: every day at 21:00
Skill: nomad-finance
Output:
- dashboard/budget.json
```

역할:

- 지출 속도 이상 감지
- 과소비 원인 정리
- 다음 날 조정 제안

## Content Harvest

```txt
Schedule: twice a week
Skill: nomad-creator
Output:
- data/content/content-ideas.json
- reports/weekly/content-harvest.md
```

역할:

- 최근 경험에서 콘텐츠 후보 추출
- 블로그/스레드/인스타 소재 분리

---

# Tool / Integration Strategy

## Initial Tools

초기에는 다음 도구만 사용한다.

```txt
Local Files
CSV
Markdown
JSON
Image files
Terminal scripts
```

## Near-Term Integrations

```txt
Google Calendar
Google Sheets
Apple Shortcuts
iCloud Drive
Photos folder
Weather API
OpenAI Vision API
Speech-to-text
```

## Mid-Term Integrations

```txt
MCP filesystem
MCP Google Calendar
MCP Google Sheets
MCP browser
Apple Notes
Apple Reminders
Git logs
Codex CLI
Claude Code CLI
```

## Later Integrations

```txt
HealthKit
Apple Watch data
SNS API
Maps / Places API
Email parsing
Browser automation
```

---

# Visualization Requirements

시각화는 핵심 기능이다.

반드시 포함해야 할 차트:

## 1. Life Balance Radar

영역별 현재 상태를 보여준다.

```txt
AI Work
Creator
Travel
Health
Food
Finance
English
Rest
```

목표는 완벽한 균형이 아니다. 현재 삶이 어디에 쏠려 있는지, 의도적으로 내려놓은 영역은 무엇인지, 위험해지는 영역은 무엇인지 보여준다.

## 2. Weekly Focus Distribution

이번 주 에너지와 시간 배분을 보여준다.

## 3. Budget Burn Rate

전체 예산 대비 현재 지출 속도를 보여준다.

## 4. Meal Balance Board

관리식과 즐기는 식사 비율을 보여준다.

## 5. Recovery vs Productivity

작업 성과와 회복 상태의 균형을 보여준다.

## 6. Experience Timeline

노마드 생활의 주요 경험과 변화 흐름을 보여준다.

## 7. Action Suggestions

에이전트가 제안한 실행 후보와 승인 상태를 보여준다.

---

# Web App Requirements

웹앱은 Hermes 결과를 보여주는 cockpit이다.

## Required Screens

### 1. Quick Capture

- 텍스트 입력
- 음성 텍스트 입력
- 사진 업로드
- 지출 빠른 입력
- 하루 체크인

### 2. Today Dashboard

- 오늘의 핵심 브리프
- 집중할 것
- 내려놓아도 되는 것
- 오늘의 리스크
- 추천 미션 3개

### 3. Agent Council

각 Agent의 판단을 카드로 보여준다.

```txt
Finance Agent
Food Agent
Health Agent
Work Agent
Travel Guide Agent
Creator Agent
English Agent
Rest Agent
```

### 4. Life Dashboard

- Life Balance Radar
- Budget Burn Rate
- Meal Balance
- Recovery vs Productivity
- Weekly Focus Distribution

### 5. Weekly Review

- 이번 주 요약
- 잘 된 영역
- 부족한 영역
- 다음 주 전략
- 콘텐츠 후보
- 리스크

### 6. Action Center

- 에이전트가 제안한 실행 후보
- 승인 필요 여부
- 실행 결과
- 실패 로그

---

# MVP Scope

Hermes 기반 MVP는 웹앱보다 Skill + Cron + Data Folder를 먼저 만든다.

## MVP 0. Hermes Setup

```txt
Hermes 설치
CLI 기본 사용
파일 읽기/쓰기 테스트
AGENTS.md 로드 확인
```

## MVP 1. Hermes Nomad Core

```txt
AGENTS.md
data folder
nomad-coordinator skill
nomad-quick-capture skill
nomad-finance skill
nomad-food skill
daily brief generation
dashboard/today.json export
```

## MVP 2. Basic Nomad Dashboard

```txt
Quick Capture UI
Today Dashboard
Agent Council
Life Dashboard
dashboard JSON 읽기
```

## MVP 3. Work + Rest

```txt
nomad-work skill
nomad-rest skill
작업/휴식 균형 분석
Recovery vs Productivity
```

## MVP 4. Health

```txt
nomad-health skill
운동 수동 입력
운동 export import
Health Dashboard
```

## MVP 5. Travel Guide

```txt
nomad-travel-guide skill
캘린더 기반 일정 확인
여행 리스크 체크
준비물 체크
```

## MVP 6. Creator + English

```txt
nomad-creator skill
nomad-english skill
콘텐츠 후보 생성
생활 기반 영어 미션 생성
```

## MVP 7. External Integrations

```txt
Google Calendar
Google Sheets
Apple Shortcuts
Photos
Weather
Vision API
Speech-to-text
```

## MVP 8. Approve-to-Act

```txt
캘린더 일정 추가
리마인더 생성
메모 저장
콘텐츠 초안 생성
Action Center
Action Log
```

---

# Development Priority

초기 개발 우선순위:

```txt
1. Hermes 설치 및 기본 실행
2. 프로젝트 폴더 구조 생성
3. AGENTS.md 배치
4. data 폴더 표준화
5. nomad-coordinator skill 작성
6. nomad-quick-capture skill 작성
7. nomad-finance skill 작성
8. nomad-food skill 작성
9. daily brief 생성
10. dashboard/today.json 생성
11. 웹앱 cockpit 개발
12. iPhone/iPad quick input 연결
13. Cron 자동화
14. 외부 API/MCP 연결
15. 승인 기반 액션 추가
```

---

# Agent Behavior Rules

에이전트는 사용자를 통제하지 않는다.

## Do

- 제안한다
- 조율한다
- 이유를 설명한다
- 부족한 영역을 부드럽게 알려준다
- 오늘 집중할 것을 줄여준다
- 내려놓아도 되는 것을 말해준다
- 실행 전 필요한 경우 승인을 요청한다
- 불확실한 데이터는 불확실하다고 표시한다
- 실행 로그를 남긴다

## Do Not

- 모든 목표를 강제하지 않는다
- 매일 모든 영역을 수행하라고 하지 않는다
- 사용자를 비난하지 않는다
- 과도한 기록을 요구하지 않는다
- 확실하지 않은 자동 분석을 단정하지 않는다
- 승인 없이 중요한 앱 데이터를 수정하지 않는다
- 금융, 건강, 일정 관련 중요한 액션을 무단 실행하지 않는다
- 불필요하게 긴 리포트를 매일 생성하지 않는다

---

# Example User Flow

## Input

```txt
오늘은 오전에 카페에서 4시간 작업했고,
점심은 12만 루피아 썼어.
맛은 좋았는데 좀 무거웠고,
수영은 못 했어.
저녁에는 친구를 만나서 돈을 좀 썼고,
영어는 거의 못 했어.
```

## Quick Capture Parsing

```txt
AI Work:
4시간 작업 기록

Finance:
점심 12만 루피아 + 저녁 추가 지출

Food:
점심 만족도 높음, 무거운 식사

Health:
수영 못 함

English:
영어 학습 부족

Rest:
소셜 활동 후 피로 가능성

Creator:
카페 작업과 친구 만남은 콘텐츠 소재 가능
```

## Agent Council

```txt
Work Agent:
작업 흐름은 좋음. 내일은 작업을 유지하되 시간은 3시간 이내 추천.

Finance Agent:
식비와 소셜 지출이 높음. 내일은 저비용 식사 추천.

Food Agent:
즐기는 식사 비중이 높음. 관리식 필요.

Health Agent:
운동 부족. 하지만 피로도 확인 필요.

English Agent:
오늘 영어 학습은 부족하지만 내일 10분 표현 복습으로 충분.

Rest Agent:
소셜 활동과 작업 시간이 모두 있었으므로 회복 필요.
```

## Coordinator Output

```txt
오늘은 AI 작업과 소셜 활동은 충분했습니다.
반면 운동, 영어, 식단 관리는 부족했습니다.

다만 모든 것을 내일 보완하려고 하기보다,
내일은 식단과 회복 중심으로 조정하는 것이 좋습니다.

내일 추천:
1. 오전 AI 작업 2~3시간
2. 점심은 가벼운 관리식
3. 오후 수영 30분
4. 영어는 10분 표현 복습만
```

## Optional Action Suggestions

```txt
[내일 오후 5시 수영 일정 추가]
[영어 표현 3개 복습 카드 생성]
[이번 주 식비 리포트 보기]
[오늘 경험으로 콘텐츠 후보 생성]
```

---

# Non-Goals for Initial Version

초기 버전에서 하지 않을 것:

```txt
완전 자동 자율 실행
은행/카드사 직접 연동
SNS 자동 게시
실시간 HealthKit 연동
완전한 네이티브 iOS 앱
복잡한 OAuth 연동
지도 기반 고급 추천
무승인 캘린더/메모 수정
```

초기 목표는 Hermes 기반 개인 생활 운영 에이전트 하네스의 가능성을 검증하는 것이다.

---

# Success Criteria

초기 성공 기준:

```txt
1. 하루 기록을 1분 이내에 입력할 수 있다.
2. 입력이 자동으로 여러 영역으로 분류된다.
3. Hermes가 daily brief를 생성한다.
4. Finance/Food/Coordinator 분석이 유의미하다.
5. dashboard/today.json이 생성된다.
6. 웹앱에서 오늘의 조율안을 확인할 수 있다.
7. 주간 리뷰에서 실제 생활 패턴이 보인다.
8. 사용자가 다음 행동을 쉽게 선택할 수 있다.
```

장기 성공 기준:

```txt
1. 사용자가 모든 데이터를 직접 분류하지 않아도 된다.
2. 에이전트가 반복 작업을 스킬화한다.
3. 캘린더, 가계부, 건강 데이터, 사진, 작업 로그가 연결된다.
4. 자동 실행과 승인 기반 실행이 안정적으로 작동한다.
5. 사용자는 노마드 생활의 방향성과 우선순위를 쉽게 파악한다.
6. 단순 기록이 아니라 생활 조율 경험을 제공한다.
```
