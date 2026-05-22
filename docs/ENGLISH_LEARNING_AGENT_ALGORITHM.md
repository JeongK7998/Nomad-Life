# English Learning Agent Algorithm

Nomad English Agent는 리뷰 문서 viewer가 아니다. 매일 축적되는 GPTs 학습 리뷰를 읽고, 반복되는 문제를 추적하며, 다음 학습 전에 GPTs가 다시 확인해야 할 문제를 되돌려주는 학습 운영 agent다.

## Review Loop

```txt
GPTs study session
  -> GPTs review JSON/MD import
  -> Normalize review events
  -> Update issue tracker
  -> Detect recurrence / improvement / unresolved issues
  -> Generate remediation plan
  -> Generate pre-study context for next GPTs session
  -> Next GPTs session tests active issues
```

## Core Objects

### Review Event

리뷰 문서에서 추출하는 최소 사건 단위다.

- `correction`: 사용자가 말한 표현과 추천 표현
- `weak_point`: 문장 구조, 어휘 정확도, 질문 구조, 자연스러움, 유창성 같은 약점
- `habit`: 반복 말하기 습관
- `strength`: 개선 또는 강점 신호
- `learned_item`: 새로 배운 표현
- `issue_test`: pre-study context로 전달한 issue가 이번 세션에서 실제로 테스트됐는지와 재발했는지

Required event fields:

- `type`
- `category`
- `issue_id`
- `evidence`
- `trigger`
- `severity`
- `confidence`
- `is_repeated`
- `is_new`

The English Agent can only judge improvement if GPTs distinguishes `not_seen` from `not_tested`.

### Issue

English Agent가 추적하는 문제 단위다. 같은 유형의 correction, weak point, habit이 여러 리뷰에서 반복되면 하나의 issue로 묶는다.

Issue fields:

- `issue_id`
- `category`: `sentence_structure | vocabulary_precision | question_structure | natural_phrasing | fluency | auxiliary_verb | word_choice | habit`
- `title`
- `status`: `watch | active | persistent | improving | resolved_candidate`
- `severity`: `low | medium | high`
- `first_seen`
- `last_seen`
- `observation_count`
- `active_day_count`
- `recent_observation_count`
- `examples`
- `remediation`
- `verification_prompt`

## Issue Detection

1. Normalize all review records up to the target date.
2. Convert every correction, weak point, non-positive habit, and `observations[]` item into an issue observation.
3. Fingerprint each observation by normalized category and `fingerprint_hint` when available.
4. Merge observations with the same fingerprint.
5. Keep examples short: original phrase, better phrase, source date.

Preferred fingerprint sources, in order:

1. `issue_id` from pre-study context
2. `issue_candidate.fingerprint_hint`
3. normalized observation category
4. fallback category inferred from correction text

## Status Rules

- `watch`: observed once, not enough data to call it a pattern.
- `active`: observed at least twice or appeared in the latest review.
- `persistent`: observed across at least two active days, or at least three total observations.
- `improving`: observed earlier, then `issue_recurrence` reports `partially_improved` or `not_seen` after an explicit test.
- `resolved_candidate`: previously persistent, explicitly tested and `not_seen` in at least 3 recent sessions. Do not call it fully resolved without more data.

Important: positive habits such as continuing despite uncertainty must be stored as improvement signals, not issues.

Important: absence of an issue is not evidence of improvement unless GPTs reports `not_seen` after testing it. Missing data is `not_tested`.

## Remediation

Each active issue gets a small drill, not a generic study plan.

Examples:

- `sentence_structure`: split one long idea into two short English sentences.
- `vocabulary_precision`: replace guessed words with known fallback descriptions.
- `question_structure`: practice fixed starts like `Can I...`, `Do you have...`, `What should I...`.
- `auxiliary_verb`: drill `do/don't`, `does/doesn't`, `did/didn't`.

## Pre-Study Context

Before the next GPTs session, English Agent should generate a short context block that can be pasted into GPTs.

It should include:

- roleplay-only mode instruction
- current active issues
- examples from previous sessions
- what GPTs should silently observe during the roleplay
- how GPTs should report recurrence after the session

GPTs should be asked to mark whether each active issue:

- reappeared
- partially improved
- did not appear
- could not be tested

The GPTs output must include `issue_recurrence[]` for every issue in the pre-study context. This is what lets the English Agent detect whether an issue is persistent, improving, or merely untested.

Important: pre-study context must not make GPTs teach during the live conversation. All correction, scoring, and issue testing should happen silently during roleplay and be reported only after the session.

## Output Contract

`dashboard/english.json` should expose:

- `learning_profile`: cumulative interpretation
- `issue_tracker`: issue registry and recurrence checks
- `pre_study_context`: copyable next-session prompt for GPTs

The Dashboard should prioritize these agent outputs over raw review lists.

## GPTs Input Requirements

For the English Agent to produce useful analysis, GPTs reviews must provide structured data rather than prose-only feedback.

Minimum required for useful issue tracking:

- session metadata: date, duration, focus area, scenario
- short transcript summary, not full transcript
- correction observations with original phrase, better phrase, category, and reason
- weak point observations with evidence and severity
- habit observations with stable snake_case habit ids and polarity
- learned items with examples
- issue recurrence results for every issue supplied in pre-study context
- new issue candidates with fingerprint hints
- session-level performance scores for vocabulary, sentence structure, natural phrasing, question structure, auxiliary verbs, fluency, pronunciation, listening, and confidence
- turn-level assessments for meaningful user answers, especially when a correction or issue appears

Without `issue_recurrence`, English Agent can detect repeated mistakes but cannot safely claim improvement or resolution.

Without `performance_scores`, the Dashboard may only show derived issue-observation scores. Real performance trends require GPTs to score the same categories consistently every session.
