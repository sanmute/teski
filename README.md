# Teski – Deadline Shamer + Deep Learning Lab

Teski keeps students honest about deadlines *and* nudges them toward deeper understanding. It now ships with:

- FastAPI + SQLModel backend (memory API, feedback service, deep-learning endpoints, prefs, analytics jobs)
- Vite + React 18 frontend (shadcn-ui/Tailwind) with Admin Cost panel, Deep Learning Lab, push-ready PWA shell
- LLM-powered feedback + elaboration + concept maps, gated by per-user opt-in preferences (GDPR friendly)

## Highlights

| Area | Capabilities |
| ---- | ------------ |
| Tasks & Planner | ICS import, reminders, APScheduler sweepers, push notifications |
| Feedback | `/feedback/generate` routed through OpenAI/Anthropic/local models with monthly cap guard + caching |
| Deep Learning Pack | Self-explanations (text/voice/Whisper), elaborative prompts, concept maps, confidence logs, interleaving toggle |
| Preferences | `/prefs/get|set` stores user opt-ins for LLM/STT/storage features; core planner stays on |
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
1. Clone & enter repo
   ```bash
   git clone https://github.com/sanmute/teski.git
   cd teski
   ```
2. Python venv
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install deps
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```
4. Env files (see `.env.example` for full list):
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
- API docs: http://localhost:8000/docs
- React app: http://localhost:5173 (dev server proxies `/api`, `/feedback`, `/analytics`, `/prefs`, `/deep`, etc.)

To serve from FastAPI only (no dev server):
```bash
cd frontend && npm run build
uvicorn app.main:app --env-file .env --port 8000
```
Static files under `frontend/dist` will be served by FastAPI’s StaticFiles mount (configure in deployment).

## Demo Flow (suggested)
1. `make dev` → wait for Uvicorn + Vite ready logs.
2. Open http://localhost:5173.
3. Import an ICS file *or* toggle “Demo mode” via Settings to show mock tasks.
4. Mark a task done → watch the “Tasks of Shame” UI update, show undo flow.
5. Open “Admin panel” link → `/admin/costs` page with cost/cache charts + KPIs.
6. In Settings (gear icon) scroll to **Deep-learning pack** toggles, turn on LLM feedback/voice/etc.
7. Browse to `/deep` (“Deep learning lab” link) to show ExplainCard, ConceptMapWidget, CalibrationChip.
8. (Optional) Hit `/feedback/admin/stats/*`, `/analytics/admin/kpis`, or `/prefs/*` via Thunder Client/Postman to highlight APIs.

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