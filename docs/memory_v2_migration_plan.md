# Teski Memory Migration Plan

## Overview

Goal: replace the legacy synchronous SQLModel schema and services under `backend/` with the new async-first architecture in `app/`. This document captures schema differences, migration tasks, and rollout stages to reach the new stack without breaking production.

---

## 1. Schema Diff (Legacy → New)

### Core Entities

| Legacy table | Key | Notes | New table | Key | Notes |
|--------------|-----|-------|-----------|-----|-------|
| `user` | INT PK, `email`, `display_name`, `created_at` (tz-aware) | Many services rely on incremental IDs; persona stored elsewhere | `user` | UUID PK, `timezone`, `streak_days`, `persona` inline, `created_at` (UTC) |
|  |  |  | `legacy_user_map` | INT legacy key → UUID | Mapping table to maintain references during migration |
| `task` | String PK (`id`), mixed sources, many extra columns (priority, status, etc.) | Includes scheduling fields, signals JSON | `task` | UUID PK, scoped to user, minimal fields (`title`, `course`, `due_at`, `created_at`) |
|  |  |  | `legacy_task_map` | Legacy string ID → UUID | Helps dual-write & backfill |
| `personas` | Persona definitions (config JSON) | Remains; still required | `personastate` | Tracks per-user persona + warmup timestamp |
| `reminder` | Reminder history | TBD port or supersede | *(tbd)* | |

### Memory / Practice

| Legacy | Notes | New |
|--------|-------|-----|
| `mistake_logs` (INT PK, template-based) | Uses template codes & instances | `mistake` (UUID PK, concept + subtype enum, raw text) |
| `memory_stats` | Skill aggregates | Superseded by SRS metrics (`memoryitem`, `reviewlog`) |
| `resurface_plans` + `review_cards` | Lightweight resurfacing queue | `memoryitem` (SM2-like) + `reviewlog` (full history) |
| `points` / `weeklyscore` | Leaderboard remains separate | `xpevent` consolidates XP events |
|  |  |  | dual-write from leaderboard + mastery bonus (via bridge) |

### Analytics / AB Testing

| Legacy | Notes | New |
|--------|-------|-----|
| None | - | `analyticsevent`, `abtestassignment`, `badge` |

### Summary of Column Changes

* Switch from integer/string IDs to UUID (`CHAR(32)` for SQLite).
* Embed persona state into `user` + `personastate`.
* Replace template-coded mistakes with concept-based memory items.
* Introduce explicit review logs and XP events.

---

## 2. Migration Strategy

### 2.1 Prerequisites

1. **Backups**  
   - Dump current `backend/app.db` (SQLite) or production database.  
   - Verify restore procedure.

2. **Staging Environment**  
   - Clone production data, run migration end-to-end, validate results.

3. **Feature Flags**  
   - `TESKI_MEMORY_V2_ENABLED`: gate new endpoints/reads.  
   - `TESKI_DUAL_WRITE`: toggle writing to both schemas.  
   - `TESKI_ASYNC_DB_URL`: configure new async engine.

### 2.2 Migration Steps

| Step | Description | Owner | Status |
|------|-------------|-------|--------|
| 1 | Create new tables (`app/models.py`) via Alembic migration (see `app/migrations/versions/0001_create_app_tables.py`) | backend | completed |
| 2 | Data backfill scripts: users, tasks, memory, XP, analytics (`scripts/backfill_memory_v2.py`) | backend | in progress |
| 3 | Dual-write adapters in legacy services (mistake logging, review scheduling, XP) | backend | completed |
| 4 | Deploy with dual-write + flag off. Monitor writes to new tables. | ops | pending |
| 5 | Build async FastAPI router using `app/db.py` + `app/scheduler` | backend | pending |
| 6 | Switch read paths (under flag) to new tables; run regression suite | backend | pending |
| 7 | Toggle flag on in staging → prod. Monitor metrics. | ops | pending |
| 8 | Remove legacy tables/models after stabilization | backend | pending |

### 2.3 Data Backfill Details

* **Users**: map legacy INT IDs to generated UUIDs. Maintain lookup table (`legacy_user_id` → `uuid`). Update downstream references during migration.
* **Tasks**: generate new UUID per existing task; carry over essential fields (title, course, due date). Some columns (priority, status) need JSON blob or dedicated columns if still required.
* **Mistakes / Memory**:
  - Convert each `mistake_logs` row into `mistake` with `concept` derived from template or skill.
  - Seed `memoryitem` per user+concept with conservative defaults (ease=2.5, interval=1, due_at=now).
  - Replay recent history into `reviewlog` where possible (using `resurface_plans` + `review_cards` + `task_attempts`).
  - Dual-write bridge now active for new mistakes & reviews; verify new tables populate before cutover.
* **XP / Analytics**: translate `pointsevent` into `xpevent` (reason mapping). Dual-write bridge logs ongoing XP events; analytics still via logging until schema wired in.

---

## 3. Rolling Implementation Plan

1. **Week 0 (Prep)**  
   - Finalize schema diff (this doc).  
   - Write Alembic migration to create new tables (`alembic revision --autogenerate` after registering models).  
   - Implement UUID mapping utilities.

2. **Week 1 (Dual-write)**  
   - Update legacy services: `log_mistake`, `mark_mastered`, `build_resurface_plan`, XP awarding to also call new async APIs using `asyncio.run` or background tasks.  
   - Add metrics/logging for new writes.

3. **Week 2 (API Cutover)**  
   - Expose new endpoints (async) mirroring legacy memory endpoints.  
   - Feature flag switch to route read traffic to new stack.  
   - Run full regression + load tests.

4. **Week 3 (Clean-up)**  
   - Remove dual-write, deprecate legacy tables, update docs.  
   - Archive old DB snapshots.

---

## 4. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| UUID migration breaks foreign keys | Maintain mapping tables; migrate child records in staged transactions |
| Async engine introduces connection issues | Load test in staging, configure connection pool limits |
| Data loss during migration | Take verified backups; dry-run migration scripts on copies |
| Feature regression (e.g., leaderboards, persona messaging) | Automated tests + manual QA while dual-write is active |

---

## 5. Next Actions

1. Generate Alembic migration for new schema (without dropping legacy tables).  
2. Implement user/task ID mapping utilities.  
3. Build dual-write wrappers for memory logging & reviews.  
4. Instrument monitoring/analytics for new tables.  
5. Schedule staging migration rehearsal.

---

*Document maintained by backend team. Update as tasks progress.* 
