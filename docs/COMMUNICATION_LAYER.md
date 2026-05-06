# Communication Layer

Nomad Life separates data capture, Dashboard viewing, Quick Panel input, conversation, and notification.

The user should not need to talk to every domain agent directly. The user talks to the Coordinator. The Coordinator reads context, consults domain Skills conceptually, and returns a single coherent answer.

## Channels

```txt
Capture Channel
  Supabase capture queue / Web Quick Capture / Telegram explicit capture / fallback local inbox
  -> fast data entry

Dashboard Channel
  Nomad Dashboard on Vercel / Local Dashboard on Mac
  -> dashboard, reports, action center, logs

Quick Panel Channel
  Workout Quick / Capture Quick / Meal Quick
  -> fast structured input from Mac, iPad, iPhone

Conversation Channel
  Hermes chat, initially local CLI simulation and later Telegram
  -> questions, planning, review, discussion

Notification Channel
  Hermes Telegram notification, later cron-driven
  -> brief, risk, opportunity, approval-needed alerts
```

Finance is not a Quick Panel input channel. The user keeps entering expenses in the existing finance app, and Nomad Life imports/downloads read-only expense data for analysis.

## Conversation Rule

The Coordinator is the only user-facing conversational agent.

The user may ask:

```txt
이번 주 일정 보고 작업하기 좋은 날 알려줘.
오늘 노트와 캘린더 기준으로 뭐부터 하면 좋을까?
이번 주 너무 과한 일정이 있는지 봐줘.
내가 오늘 남긴 기록을 기준으로 내일 계획을 정리해줘.
```

The Coordinator may internally use:

```txt
nomad-calendar-context
nomad-notes-context
nomad-quick-capture
nomad-work
nomad-rest
nomad-travel-guide
nomad-finance
nomad-food
```

But the final response must stay unified.

## Telegram Capture Rule

Telegram is primarily the Conversation Channel, but it may also create Quick Captures when the user explicitly marks a message as capture input.

Accepted capture prefixes are plain text prefixes, not Telegram slash commands.

```txt
캡쳐: 오늘 2시간 코딩했고 집중도는 좋았음
기록: 택시비 18000원
저장: 내일 병원 다녀온 뒤 회복 시간 필요할 듯
capture: 오늘 점심은 무거웠고 커피까지 마심
```

Do not use `/capture`. Hermes gateway treats unknown slash-prefixed messages as gateway commands before they reach the Coordinator.

When a Telegram message uses one of these prefixes, the Coordinator should:

1. Remove the prefix.
2. Save the remaining text through `scripts/quick_capture.py --text "..."`
3. Let the default post-capture refresh update dashboard and notification candidates. Finance refresh happens through external finance app export/read-only import, not capture-based expense entry.
4. Confirm the capture id, linked agents, confidence, and any generated review candidate briefly.
5. Avoid treating the same message as a normal planning question unless the user also asks for analysis.

If a message sounds like a record but has no explicit capture prefix, the Coordinator may ask whether to save it, but should not automatically persist it.

## Notification Rule

Notifications should be sparse and useful.

Notification generation has two separate steps:

```txt
candidate generation
  -> dashboard/notifications.json
  -> no external send

transport
  -> Telegram or another channel
  -> approval-aware sending
```

Initial implementation only creates candidates. It does not send Telegram messages.

Good notifications:

```txt
오늘은 시간 지정 일정이 1개뿐이라 90분 작업 블록을 넣기 좋습니다.
Notes에 작업 후보가 하나 들어왔지만 본문은 읽지 않았습니다. 필요하면 capture로 전환하세요.
이번 주 일정 밀도가 높은 날이 있어 회복 시간을 먼저 보호하는 게 좋습니다.
```

Bad notifications:

```txt
운동하세요.
영어 하세요.
식단 관리하세요.
모든 목표를 오늘 완료하세요.
```

## Authority

Conversation may:

- Read normalized local context.
- Summarize dashboard and reports.
- Explain uncertainty.
- Propose actions.
- Draft plans or messages for user review.

Conversation must not:

- Modify Calendar, Notes, Reminders, or external apps without explicit approval.
- Treat partial snapshots as complete truth.
- Send messages or post content without confirmation.
- Push frequent nagging alerts.
- Break the Coordinator single-channel rule.

## Local Test Entry Point

Before Telegram is enabled, Coordinator Chat can be tested locally:

```bash
scripts/run_hermes_coordinator_chat.py "이번 주 일정 보고 작업하기 좋은 날 알려줘."
```

The script is read-only.

## Telegram Target

Later, Telegram should call the same Coordinator prompt contract:

```txt
Telegram message
  ↓
Hermes Coordinator Chat
  ↓
read dashboard/context/reports
  ↓
Coordinator response
```

Telegram is not a data store. Important user-provided data should still be saved through Quick Capture, Supabase queue, or explicitly converted into a capture.
