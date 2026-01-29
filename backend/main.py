from pathlib import Path
from dotenv import load_dotenv

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(BASE_PATH / ".env", override=False)
load_dotenv(BASE_PATH / ".env.backend", override=True)

import sys
import os
PROJECT_ROOT = BASE_PATH  # repo root (/app)
root_str = str(PROJECT_ROOT)
if root_str in sys.path:
    sys.path.remove(root_str)
sys.path.insert(0, root_str)
parent_str = str(PROJECT_ROOT.parent)
if parent_str not in sys.path:
    sys.path.insert(1, parent_str)
# Fallback for app package settings in environments missing secrets (keeps imports from failing)
os.environ.setdefault("TESKI_SECRET_KEY", "dev-placeholder-secret")
from fastapi import FastAPI, Depends, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from routes import tasks as tasks_route
from routes import reminders as reminders_route
from routes import health as health_route
from routes import studypack as studypack_route
from routes import integrations as integrations_route
from routes import memory as memory_route
from routes import estimates as estimates_route
from routes import topics as topics_route
from routes import analytics as analytics_route
from routes import exercises as exercises_route
from routes import stats as stats_route
from routes import push as push_route
from routes import microquest as microquest_route
from routes import leaderboard as leaderboard_route
from routes import onboarding as onboarding_route
from routes import feedback as feedback_route
from routes import explanations as explanations_route
from db import init_db, get_session
from sqlmodel import Session
from services.seeder import load_seed
from schemas import MockLoadResp

ALLOW_ORIGINS = [
    "https://teski.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

init_db()
app = FastAPI(title="Deadline Agent Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def ensure_cors_on_error(request: Request, call_next):
    """
    Safety net to keep CORS headers on error responses (e.g., 500s) so browsers
    don't mask JSON errors with CORS failures.
    """
    origin = request.headers.get("origin")
    try:
        response = await call_next(request)
    except Exception as exc:  # pragma: no cover - last-resort guard
        response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    if origin in ALLOW_ORIGINS and "access-control-allow-origin" not in response.headers:
        response.headers["access-control-allow-origin"] = origin
        response.headers["access-control-allow-credentials"] = "true"
    return response

from routes import debug_db as debug_db_route
app.include_router(debug_db_route.router)

# app/backend/main.py
from routes import import_ics as import_ics_route
app.include_router(import_ics_route.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(tasks_route.router)
api_router.include_router(reminders_route.router)
api_router.include_router(studypack_route.router)
api_router.include_router(integrations_route.router)
api_router.include_router(memory_route.router, prefix="/v1")  # backward-compatible /api/v1/memory
api_router.include_router(memory_route.router)
api_router.include_router(estimates_route.router)
api_router.include_router(topics_route.router)
api_router.include_router(push_route.router)
api_router.include_router(microquest_route.router)
api_router.include_router(leaderboard_route.router)
api_router.include_router(analytics_route.router)
api_router.include_router(exercises_route.router)
api_router.include_router(stats_route.router)
api_router.include_router(onboarding_route.router)
api_router.include_router(feedback_route.router)
api_router.include_router(explanations_route.router_api)

app.include_router(health_route.router)
from routes import auth as auth_route
app.include_router(auth_route.router)
api_router.include_router(auth_route.router)
app.include_router(explanations_route.router)
app.include_router(explanations_route.router_compat)

from routes import users as users_route
app.include_router(users_route.router)

# >>> PERSONA START
from routes import persona as persona_route

app.include_router(persona_route.router)
# <<< PERSONA END

# >>> DFE START
from routes import dfe_tasks as dfe_tasks_route

app.include_router(dfe_tasks_route.router)
# <<< DFE END
# >>> INSTITUTIONS START
from routes import institutions_admin as institutions_admin_route
from routes import educator as educator_route

app.include_router(institutions_admin_route.router)
app.include_router(educator_route.router)
# <<< INSTITUTIONS END

# >>> MEMORY V1 START
from routes import memory_v1 as memory_v1_route

app.include_router(memory_v1_route.router)
# <<< MEMORY V1 END

# Mount aggregated API routes after all potential inclusions.
app.include_router(api_router)

# mock loader for demo
misc = APIRouter(prefix="/api", tags=["misc"])

@misc.post("/tasks/mock-load", response_model=MockLoadResp)
def mock_load(session: Session = Depends(get_session)):
    loaded = load_seed(session)
    return MockLoadResp(loaded=loaded)

app.include_router(misc)

# in main.py
from apscheduler.schedulers.background import BackgroundScheduler
from db import get_session, engine
from sqlmodel import Session
from services.reminder_engine import run_sweep

scheduler = BackgroundScheduler()
def job():
    with Session(engine) as s:
        run_sweep(s, persona="teacher")
scheduler.add_job(job, "interval", minutes=15)
scheduler.start()

# >>> SEED EXERCISES START
from seed.exercises_intro_python import seed_intro_python_exercises

@app.on_event("startup")
def seed_intro_python():
    with Session(engine) as session:
        seed_intro_python_exercises(session)
# --- debug: log key API routes at startup so we know they are mounted in prod ---
@app.on_event("startup")
def log_key_routes():
    logger = logging.getLogger("startup.routes")
    targets = [r.path for r in app.router.routes if r.path.startswith("/api/")]
    logger.warning("Mounted /api routes (%d): %s", len(targets), sorted(set(targets)))
# <<< SEED EXERCISES END

# Backward compatibility: allow legacy clients hitting /tasks/upcoming without /api prefix
from routes.tasks import list_upcoming as list_upcoming_tasks  # type: ignore

@app.get("/tasks/upcoming", include_in_schema=False)
def upcoming_compat(session: Session = Depends(get_session)):
    return list_upcoming_tasks(session=session)
