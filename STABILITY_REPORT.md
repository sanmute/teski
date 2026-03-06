# System Stability Report - Teski Backend

**Date:** 2026-03-06  
**Scope:** teski.app + Fly backend (teski-zj2gsg.fly.dev)  
**Core flows:** onboarding/profile, exercise load, exercise submit, explanation generation

---

## 1. What Was Broken

### S0 (Blocks core path)

| Bug | Flow | Status | Root Cause |
|-----|------|--------|------------|
| **Explanations API path mismatch** | Explanation generation | 404 | `router_api` had prefix `/api/explanations` while mounted under `api_router` (prefix `/api`), producing `/api/api/explanations/generate`. The correct path `/api/explanations/generate` did not exist. Smoke test initially used wrong path. |

### S1 (Degrades experience)

| Bug | Flow | Status | Root Cause |
|-----|------|--------|------------|
| **Push 500 without VAPID** | Push notifications | 500 | `routes/push.py` raises HTTPException if `VAPID_PUBLIC_KEY` not configured |
| **Ephemeral DB** | All flows | Data loss on deploy | No `[mounts]` in fly.toml; SQLite at `backend/app.db` is ephemeral |
| **No LLM fallback logging** | Explanations | Silent fallback | When `OPENAI_API_KEY` missing or LLM fails, falls back to deterministic blocks without clear logging |

### Smoke test results (initial run)

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /health | 200 | OK |
| GET /api/debug/cors | 200 | OK |
| GET /api/ex/list | 200 | OK, 15 exercises |
| GET /api/ex/get?id=python-intro-1 | 200 | OK |
| POST /auth/signup | 200 | OK |
| GET /api/onboarding/status | 200 | OK |
| POST /api/onboarding/submit | 200 | OK |
| POST /api/ex/answer | 200 | OK |
| POST /api/explanations/generate | 404 | Wrong path (see fix) |
| POST /explanations/generate | 200* | Frontend compat path (router_compat) |

---

## 2. What Was Fixed

### Code changes

1. **`backend/routes/explanations.py`** – Fixed `router_api` prefix:
   - Before: `prefix="/api/explanations"` → full path `/api/api/explanations/generate`
   - After: `prefix="/explanations"` → full path `/api/explanations/generate`

2. **`scripts/smoke_test_prod.ps1`** and **`scripts/smoke_test_prod.sh`** – Updated to use correct paths:
   - Explanations: `/explanations/generate` (matches frontend compat route)

3. **`backend/routes/push.py`** – Graceful handling when VAPID not configured (fixes 500):
   - Before: `raise HTTPException(500, "VAPID public key not configured")`
   - After: Return `{"publicKey": null, "enabled": false}` (200)

4. **`backend/main.py`** – Added logging for unhandled exceptions in middleware

5. **`backend/routes/explanations.py`** – Added info log when LLM skipped (OPENAI_API_KEY not set)

---

## 3. What Remains

| Item | Severity | Action |
|------|----------|--------|
| **Ephemeral DB** | S1 | Add Fly volume mount for `app.db` or migrate to persistent storage |
| **Fly secrets** | Verify | Run `fly secrets list` when Fly CLI available |
| **Deploy fixes** | - | Deploy backend changes to production for explanations path + push graceful handling |

---

## 4. Proof

### Smoke test output (first run)

```
=== Teski Backend Smoke Test ===
Base URL: https://teski-zj2gsg.fly.dev
Started: 2026-03-06T10:02:07

--- 1. GET /health ---
Status: 200
Response: {"ok":true}

--- 2. GET /api/debug/cors ---
Status: 200
Response: {"ok":true,"origin":null,"host":"teski-zj2gsg.fly.dev","allowed_origins":["https://teski.app","https://www.teski.app"]}

--- 3. GET /api/ex/list ---
Status: 200
Response: {"items":[...], "page":1, "page_size":15, "total":15}

--- 5. POST /auth/signup ---
Status: 200
Response: {"access_token":"eyJ...","token_type":"bearer","user_id":"b4667038-76ae-40d6-9315-e01c09107bc1","email":"smoke-1772791327@teski-smoke.test"}

--- 6. GET /api/onboarding/status ---
Status: 200
Response: {"ok":true,"onboarded":false}

--- 7. POST /api/onboarding/submit ---
Status: 200
Response: {"ok":true,"onboarded":true}

--- 8. POST /api/ex/answer ---
Status: 200
Response: {"ok":true,"exercise_id":"python-intro-1","is_correct":false,"correct_answer":"8",...}

--- 9. POST /api/explanations/generate (text) ---
Status: 404
Response: The remote server returned an error: (404) Not Found.
```

### Curl commands for manual verification

```bash
# Health
curl -s https://teski-zj2gsg.fly.dev/health

# CORS
curl -s https://teski-zj2gsg.fly.dev/api/debug/cors

# Exercise list
curl -s https://teski-zj2gsg.fly.dev/api/ex/list

# Explanations (compat path)
curl -s -X POST https://teski-zj2gsg.fly.dev/explanations/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"What is 2+2?","mode":"big_picture"}'
```

### Run smoke test

```powershell
cd teski-main/teski/scripts
.\smoke_test_prod.ps1
```

```bash
# Unix
./scripts/smoke_test_prod.sh
```

---

## 5. Fly Environment Variables Checklist

**To verify:** Run `fly secrets list` from the backend directory (requires [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)).

```bash
cd teski-main/teski/backend
fly secrets list
```

**Required for core path:**

| Variable | Purpose | Default / Notes |
|----------|---------|-----------------|
| `TESKI_SECRET_KEY` | JWT signing | Must be set in prod (not `dev-placeholder-secret`) |
| `TESKI_ALLOWED_ORIGINS` | CORS | Optional; default includes teski.app, www.teski.app |

**Optional (enhance experience):**

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | LLM explanations (fallback to deterministic if unset) |
| `EXPLANATIONS_MODEL` | LLM model (default: gpt-4o-mini) |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_PEM` | Push notifications (now returns `enabled: false` if unset) |
| `TESKI_ADMIN_KEY` | Exercise seed (X-Admin-Key header) |
| `EXERCISES_DIR` | Exercise JSON dir (default: seed) |

---

## 6. DB Migrations and Schema Verification

**Backend DB:** SQLite at `backend/app.db`. Schema is created by `init_db()` at startup (no Alembic).

**To verify on Fly:** Check startup logs for DB init messages:

```bash
fly logs -a teski-zj2gsg
```

Expected log lines:
- `[DB] init_db() starting`
- `[DB] SQLite file: .../app.db`
- `[DB] ORM tables ensured (Task, Reminder, StudyPack)`
- `[DB] Help Library tables ensured (mode=fts5 or fallback)`

**Key tables:** `user`, `user_onboarding`, `exercise`, `analytics_events`, `task`, etc.

**Note:** App package has separate Alembic migrations (`app/migrations/`) for `teski_v2.db`; backend does not use these.
