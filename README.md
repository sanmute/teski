# Teski – Practice, Diagnosis, and Learning Trajectories

Teski is a learning & task platform for students. It now ships with:

- FastAPI + SQLModel backend (micro-quests, memory, mastery, challenge engine v2, diagnostic engine, learning trajectories, prefs, analytics jobs)
- Vite + React 18 frontend (Today → Micro-quest → Summary loop, Skill Map, Admin Cost panel, Deep Learning Lab, push-ready PWA)
- Domain-aware diagnostic engine for Python/Math/Generic + numeric/units detector; challenge engine v2 for balanced comfort/challenge/stretch runs
- LLM-backed feedback/elaboration/concept maps (opt-in, privacy-aware)

## Highlights

| Area | Capabilities |
| ---- | ------------ |
| Tasks & Planner | ICS import, reminders, APScheduler sweepers, push notifications |
| Practice Loop | Today → personalized micro-quest → persona feedback → summary; Skill Map entry point |
| Challenge Engine v2 | Balanced comfort/challenge/stretch, new vs review mix, behavior-aware ratios |
| Diagnostic Engine | Domain-aware (math/python/generic + numeric/units) → mistake_type `family:subtype` for mastery/review/persona |
| Learning Trajectories | Mastery snapshots, session summaries, skill trajectories/trends via `/analytics/me/*` |
| Feedback | `/feedback/generate` via OpenAI/Anthropic/local models with cap + cache |
| Preferences | `/prefs/get|set` stores per-user opt-ins for LLM/STT/storage; planner stays on |
| Analytics | Raw events + daily aggregates + `/analytics/admin/kpis` for DAU/WAU, retention, paid users |
| Admin UX | `/admin/costs` page with Recharts summary of cost/cache + KPIs |

## Tech Stack
- **Backend:** FastAPI, SQLModel, Alembic, APScheduler, SQLite (default)
- **LLM/AI:** Feedback router w/ OpenAI + Anthropic + local llama, optional Whisper (OpenAI or faster-whisper)
- **Frontend:** Vite, React 18, TypeScript, Tailwind CSS, shadcn-ui components, TanStack Query, Recharts
- **Tooling:** npm, ESLint, Makefile helpers, PWA service worker

## Repo Layout
```
app/            Memory API + feedback/deep/prefs routers (FastAPI entrypoint)
backend/        Legacy planner service (tasks, reminders, push, ICS)
frontend/       React client (dashboard, admin panel, deep-learning lab)
docs/           Specs & migration notes
requirements.txt  Backend Python deps
Makefile        Convenience commands (setup, dev, lint)
```

## Setup
1) Clone & enter repo
```bash
git clone https://github.com/sanmute/teski.git
cd teski
```

2) Python venv
- macOS/Linux:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

3) Install deps
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

4) Env files (see `.env.example` for full list):
```env
DATABASE_URL=sqlite:///./teski_v2.db
FEEDBACK_MONTHLY_CAP_EUR=50.0
FEEDBACK_CAP_MODE=mini-only      # or block
ENABLE_ANALYTICS_JOBS=true
ANALYTICS_CRON=0 2 * * *
ENABLE_WHISPER=false             # true enables OpenAI/faster-whisper
OPENAI_API_KEY=sk-...
VITE_API_BASE=/
```
Generate VAPID keys if you want push notifications (set in `.env.backend` + `.env.frontend`).

## Run Locally
```bash
make dev      # runs uvicorn app.main + npm run dev simultaneously
```

### Auth (beta)
- Backend env: `TESKI_SECRET_KEY` (used for JWT signing)
- Signup: `curl -X POST http://localhost:8000/api/auth/signup -H "Content-Type: application/json" -d '{"email":"a@b.com","password":"pw"}'`
- Login (JSON): `curl -X POST http://localhost:8000/api/auth/login-json -H "Content-Type: application/json" -d '{"email":"a@b.com","password":"pw"}'`
- Me: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/auth/me`

## Exercises System (authoring, seeding, APIs)
- Author JSON files under `seed/exercises/` (you can nest subfolders). Format:
  ```json
  {
    "id": "temp-ENG_ACAD-001",
    "question_text": "...",
    "type": "multiple_choice",
    "choices": ["...","..."],
    "correct_answer": "...",
    "difficulty": 1,
    "skill_ids": ["eng_acad_tense_pres_simple_1"],
    "solution_explanation": "...",
    "hint": "...",
    "metadata": { "topic": "...", "estimated_time_seconds": 40 }
  }
  ```
- Seed (dev): `cd backend && python -m uvicorn main:app --reload` then POST `/api/ex/seed` (optionally `?path=seed/exercises`). If `TESKI_ADMIN_KEY` is set, include header `X-Admin-Key`.
- Query:
  - `curl "<BASE>/api/ex/list?user_id=UUID&difficulty_min=1&difficulty_max=5"`
  - `curl "<BASE>/api/ex/get?id=temp-ENG_ACAD-001"`
  - `curl -X POST "<BASE>/api/ex/answer" -H "Content-Type: application/json" -d '{"user_id":"UUID","exercise_id":"temp-ENG_ACAD-001","answer":"..."}'`
- API docs: http://localhost:8000/docs
- React app: http://localhost:5173 (dev server proxies `/api`, `/feedback`, `/analytics`, `/prefs`, `/deep`, etc.)

Windows alternative (no Make):
```powershell
uvicorn main:app --env-file .env --port 8000
cd frontend; npm run dev
```

To serve from FastAPI only (no dev server):
```bash
cd frontend && npm run build
uvicorn main:app --env-file .env --port 8000
```
Static assets under `frontend/dist` can be served via FastAPI StaticFiles or your web server.

## Demo Flow (suggested)
1. `make dev` → wait for Uvicorn + Vite ready logs.
2. Open http://localhost:5173.
3. Start from **Today** → Daily Practice card → Micro-quest run → Summary → back to Today (watch streak/mastery progress).
4. Open **Skill Map** → start micro-quest from a node.
5. Visit `/admin/costs` for cost/cache charts + KPIs.
6. In Settings, toggle Deep-learning pack (LLM feedback/voice) and try `/deep` lab components.
7. Optional API pokes: `/feedback/admin/stats/*`, `/analytics/admin/kpis`, `/analytics/me/recent-trends`, `/analytics/me/skill-trajectory`.

## Database & Migrations
- Default DB: `teski_v2.db` (root FastAPI service); legacy planner uses `backend/app.db`.
- Alembic configuration under `app/migrations/` targets SQLModel metadata (memory + feedback + deep + prefs tables).
- Typical cycle:
  ```bash
  alembic -c alembic.ini revision --autogenerate -m "<message>"
  alembic -c alembic.ini upgrade head
  ```

## Preferences & Privacy
- `app/prefs` stores per-user opt-ins: `allow_llm_feedback`, `allow_voice_stt`, etc.
- Deep-learning routes read these flags and return 403 when features are disabled.
- Self-explanations and concept maps only store UUID + topic/item IDs; no names/emails.
- Toggling off storage deletes access (GET returns empty data).

## Analytics & Cost Controls
- `/feedback/admin/stats/cache|costs` provide cost telemetry + cache hit rate.
- `/analytics/admin/kpis` exposes DAU/WAU, retention (7/28), avg session mins, reviews/user, paid user count.
- Nightly job (`ENABLE_ANALYTICS_JOBS=true`) runs `nightly_analytics_job` via APScheduler (cron configurable via `ANALYTICS_CRON`).
- Feedback monthly cap ensures spend stays in budget (`FEEDBACK_MONTHLY_CAP_EUR`, `FEEDBACK_CAP_MODE=mini-only|block`).

## Push Notifications (optional)
- Planner backend exposes `/api/push/*` routes with Web Push (VAPID).
- Service worker lives in `frontend/public/service-worker.js` (stale-while-revalidate strategy).
- Use HTTPS or `localhost` for subscription in Chromium.

## Testing / Linting
- Frontend lint: `cd frontend && npm run lint`
- Backend tests currently limited; add under `tests/` and run with `pytest` (not bundled yet).
- Format/lint tasks reachable via Makefile or IDE scripts.

## Deployment Notes
- Use a production ASGI server (e.g., `uvicorn --workers` behind nginx or `gunicorn -k uvicorn.workers.UvicornWorker`).
- Ensure the service worker and manifest are served from the web root.
- Configure environment variables via your hosting platform—never commit secrets.

## Contributing / Next Steps
- Open issues or pull requests for new integrations, additional reminder rules, or UI polish.
- Consider adding automated tests and CI workflows before deployment.
- Document any institution-specific integrations in `docs/` (create if needed) to share with collaborators.

Happy studying with Teski!



© 2025 Santeri Mutanen/Teski Team. All Rights Reserved.

This project, including its code, design, documentation, and related assets (“Teski”), is the intellectual property of the project authors.
	•	You may view and use the code for personal, educational, or evaluation purposes.
	•	You may not copy, modify, distribute, sublicense, or use any part of this project, in whole or in part, for commercial or non-commercial purposes without prior written consent from the authors.
	•	Unauthorized use, reproduction, or distribution of this project is strictly prohibited and may result in legal action.

If you wish to collaborate, contribute, or license this project, please contact the authors directly through semutanen@gmail.com.
