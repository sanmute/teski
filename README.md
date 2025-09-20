# Teski – Deadline Shamer Dashboard

Teski is a study companion that keeps you accountable for upcoming deadlines. The project combines a FastAPI backend, a Vite + React frontend, and a lightweight service worker to deliver reminders, push notifications, and a playful dashboard featuring Teski the deadline frog.

## Features
- Import calendar data (ICS) and turn events into trackable tasks.
- Surfaced study-pack insights, topic maps, and reminder scheduling.
- Push notification support (VAPID) with a background scheduler that periodically sweeps for new reminders.
- Responsive front end built with shadcn-ui, Tailwind CSS, and TanStack Query.
- Progressive Web App hooks (manifest + service worker) so Teski can be installed or work offline for cached assets.

## Tech Stack
- **Backend:** FastAPI, SQLModel, APScheduler, SQLite, Python 3.12
- **Frontend:** Vite, React 18, TypeScript, Tailwind CSS, shadcn-ui components
- **Tooling:** npm, ESLint, Makefile helpers, service worker caching

## Repository Layout
```
backend/        FastAPI application, database models, services, and routers
frontend/       Vite + React client, UI components, assets, service worker
requirements.txt  Python dependencies for the backend
Makefile        Common setup/build/dev commands
```

## Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- SQLite (bundled with Python, used via `sqlite:///` URL)

## Initial Setup
1. **Clone the repository**
   ```bash
   git clone <your fork or GitHub repo url>
   cd teski
   ```
2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate  # Windows: backend\.venv\Scripts\activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```
   Or run `make setup` to perform the same steps.
4. **Create environment files** (not tracked in Git):
   - `.env` (shared defaults)
     ```env
     APP_NAME=Teski
     API_PREFIX=/api
     DB_FILE=app.db
     ```
   - `.env.backend`
     ```env
     DATABASE_URL=sqlite:///backend/app.db
     SECRET_KEY=<random string>
     ACCESS_TOKEN_EXPIRE_MINUTES=60
     VAPID_PRIVATE_PEM="-----BEGIN EC PRIVATE KEY-----..."
     VAPID_PUBLIC_KEY=<matching public key>
     LOG_LEVEL=debug
     ```
   - `.env.frontend`
     ```env
     VITE_API_BASE=/api
     VITE_APP_NAME=Teski
     VITE_VAPID_PUBLIC=<same public key as above>
     ```
   Generate your own VAPID key pair for push notifications or remove push usage until you have keys.

## Running the Project
- **Backend (FastAPI + scheduler):**
  ```bash
  uvicorn backend.main:app --reload --env-file .env.backend --port 8000
  ```
  API docs live at http://localhost:8000/docs once the server is running.

- **Frontend (Vite dev server):**
  ```bash
  cd frontend
  npm run dev -- --host localhost --port 5173
  ```
  Visit http://localhost:5173 in the browser. The dev server proxies `/api` calls to the backend.

- **Run both with one command:**
  ```bash
  make dev
  ```
  Uses a background process group to boot both servers (Ctrl+C stops both).

## Building for Production
- **Frontend bundle:** `cd frontend && npm run build`
- **Compile backend bytecode (optional):** `python -m compileall backend`
- **Static assets:** The service worker (`frontend/public/service-worker.js`) precaches key files and updates with a stale-while-revalidate strategy.

## Data & Seeding
- Default storage is `backend/app.db` (SQLite). Delete the file to reset the database.
- Load mock data via the `/api/tasks/mock-load` POST endpoint; it seeds sample tasks from `backend/seed/tasks.json`.

## Push Notifications
- Teski exposes a VAPID-enabled push route (`backend/routes/push.py`).
- Serve your generated `VAPID_PUBLIC_KEY` to the client (see `.env.frontend`).
- Chromium may require HTTPS or `localhost` to allow push subscriptions.

## Testing & Linting
- Frontend linting: `cd frontend && npm run lint`
- JavaScript/TypeScript formatting: use your editor or run `eslint` per the Makefile.
- (No formal backend test suite yet; add one under `backend/tests/`).

## Deployment Notes
- Use a production ASGI server (e.g., `uvicorn --workers` behind nginx or `gunicorn -k uvicorn.workers.UvicornWorker`).
- Ensure the service worker and manifest are served from the web root.
- Configure environment variables via your hosting platform—never commit secrets.

## Contributing / Next Steps
- Open issues or pull requests for new integrations, additional reminder rules, or UI polish.
- Consider adding automated tests and CI workflows before deployment.
- Document any institution-specific integrations in `docs/` (create if needed) to share with collaborators.

Happy studying with Teski!
