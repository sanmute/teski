# Exam Planner API

## Overview

The `/exam` namespace provides tools for building personalised study plans ahead of an exam. The workflow:

1. Create an exam record for a user.
2. Attach topics with estimated effort and dependencies.
3. Submit a short questionnaire to pick a planning style.
4. Generate a study plan with scheduled blocks and optional mocks.
5. Fetch daily agendas that blend study blocks with spaced-repetition reviews.
6. Update block progress and regenerate plans when life happens.

All timestamps are UTC unless otherwise stated. Day-based scheduling respects the student’s timezone when available.

---

## Endpoints

### `POST /exam/create`

Create a new exam.

```json
{
  "user_id": "USER_UUID",
  "title": "EE Midterm",
  "course": "Basics of EE",
  "exam_at": "2025-11-01T09:00:00",
  "target_grade": 5,
  "notes": "Focus on circuits"
}
```

### `POST /exam/{exam_id}/topics`

Add one or more topics.

```json
[
  {"name": "KCL", "est_minutes": 120, "priority": 3},
  {"name": "KVL", "est_minutes": 120, "dependencies": ["KCL"]}
]
```

### `POST /exam/{exam_id}/questionnaire`

Submit Likert-style answers and optionally force a style (`style: "auto"` lets the scorer decide).

```json
{
  "style": "auto",
  "answers": {
    "pref_practice": 5,
    "topic_switching": 4,
    "cram_history": 2
  }
}
```

Response:

```json
{
  "style": "interleaved_hands_on",
  "weights": {
    "spaced_structured": 0.22,
    "cram_then_revise": 0.15,
    "interleaved_hands_on": 0.41,
    "theory_first": 0.22
  }
}
```

### `POST /exam/{exam_id}/plan`

Generate a plan. Planner options are optional.

```json
{
  "buffer_days": 2,
  "daily_cap_min": 150,
  "min_block": 25,
  "mock_count": 2,
  "interleave_ratio": 0.5
}
```

Response contains the plan metadata and scheduled blocks.

### `GET /exam/{exam_id}/plan`

Fetch the latest plan (including mock blocks and progress status).

### `GET /exam/{exam_id}/today?user_id=USER_UUID`

Returns a blended agenda for the student’s local day. Example:

```json
[
  {"kind": "review_due", "memory_id": "...", "concept": "Ohm", "due_at": "2025-10-05T07:00:00"},
  {"kind": "study_block", "block_id": "...", "topic": "KCL", "minutes": 30, "type": "learn", "status": "scheduled"}
]
```

The ordering honours `EX_AGENDA_REVIEW_FIRST` (default `true`). When disabled, reviews and study blocks interleave using `INTERLEAVE_RATIO`.

### `POST /exam/block/progress`

Update a block’s status.

```json
{
  "block_id": "...",
  "status": "done",
  "minutes_spent": 28
}
```

Transitions: `scheduled → done|skipped`. When a block is marked `done`, a small XP reward (`reason: study_block_done`) is issued. Drill/mock blocks that end early also schedule a memory review by logging a conceptual mistake.

### `POST /exam/{exam_id}/regenerate`

Rebuild the plan while carrying over previously completed blocks. Useful after missed sessions; skipped blocks are reflowed forward using `reflow_plan`.

---

## Memory Integration

- Review/drill blocks carry the topic name as a concept label.
- `/exam/{exam_id}/today` fetches due spaced-repetition reviews via the memory module and merges them into the agenda.
- When drill/mock blocks finish with insufficient time, a `Mistake` is logged and the concept is queued with `schedule_from_mistake` for early follow-up.

---

## Status Lifecycle

```
scheduled ──(complete)──▶ done
      │
      └──(skip)──────────▶ skipped
```

Only `done` blocks accrue XP. Skipped blocks remain available for regeneration/reflow.
