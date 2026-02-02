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
import os
from uuid import uuid4
import traceback
from typing import Callable
DEBUG_AUTH = os.getenv("DEBUG_AUTH", "false").lower() == "true"

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
# Backward-compat: ensure explanations_route.router exists even if older code references it
if not hasattr(explanations_route, "router"):
    explanations_route.router = explanations_route.router_api
from db import init_db, get_session
from sqlmodel import Session
from services.seeder import load_seed
from schemas import MockLoadResp

DEFAULT_ORIGINS = [
    "https://teski.app",
    "https://www.teski.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

def parse_allowed_origins(env_val: str | None) -> list[str]:
    if not env_val:
        return DEFAULT_ORIGINS
    return [o.strip() for o in env_val.split(",") if o.strip()]

ALLOW_ORIGINS = parse_allowed_origins(os.getenv("TESKI_ALLOWED_ORIGINS"))
ALLOW_ORIGIN_REGEX = r"^https://.*\\.vercel\\.app$"

init_db()
app = FastAPI(title="Deadline Agent Backend", version="0.1.0")
print("[BOOT] using app from main:app", file=sys.stderr)
print("[startup] FastAPI app created; CORS will be applied; binding via uvicorn main:app on 0.0.0.0:8080", file=sys.stderr)
app.state.allowed_origins = ALLOW_ORIGINS

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("teski")

# Log middleware stack fingerprint on boot
print("[BOOT] middleware_stack=", [m.cls.__name__ for m in app.user_middleware], file=sys.stderr)
print("[BOOT] fingerprint=TESKI_MW_V1", file=sys.stderr)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_origin_regex=ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] ,
    expose_headers=["*"],
    max_age=86400,
)

if DEBUG_AUTH:
    logging.getLogger("auth").setLevel(logging.DEBUG)
    logging.getLogger("auth").warning("DEBUG_AUTH enabled; auth failures will be logged (no tokens)")

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
    def _origin_allowed(o: str | None) -> bool:
        if not o:
            return False
        if o in ALLOW_ORIGINS:
            return True
        import re
        return bool(re.match(ALLOW_ORIGIN_REGEX, o))

    if _origin_allowed(origin) and "access-control-allow-origin" not in response.headers:
        response.headers["access-control-allow-origin"] = origin
        response.headers["access-control-allow-credentials"] = "true"
    return response

# Inject request_id on every request
@app.middleware("http")
async def fingerprint_and_exceptions(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    dbg = request.headers.get("x-teski-debug", "")
    print(f"[DBG] {request.method} {request.url.path} x-teski-debug={dbg!r}", file=sys.stderr)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["x-teski-fingerprint"] = "TESKI_MW_V1"
        response.headers["x-teski-mw-present"] = "1"
        response.headers["x-teski-debug-seen"] = dbg
        return response
    except Exception:
        tb = traceback.format_exc()
        print(f"[EXC] request_id={request_id} {request.method} {request.url.path}", file=sys.stderr)
        print(tb, file=sys.stderr)
        body = {
            "detail": "Internal Server Error",
            "request_id": request_id,
            "fingerprint": "TESKI_MW_V1",
            "debug_seen": dbg,
        }
        if dbg == "trace":
            body["traceback"] = tb
        resp = JSONResponse(status_code=500, content=body)
        resp.headers["X-Request-ID"] = request_id
        resp.headers["x-teski-fingerprint"] = "TESKI_MW_V1"
        resp.headers["x-teski-mw-present"] = "1"
        resp.headers["x-teski-debug-seen"] = dbg
        return resp

# Exception handler fallback that also sets fingerprint headers
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    body = {"detail": "Internal Server Error", "fingerprint": "TESKI_MW_V1", "request_id": request_id}
    resp = JSONResponse(status_code=500, content=body)
    resp.headers["x-teski-fingerprint"] = "TESKI_MW_V1"
    resp.headers["x-teski-mw-present"] = "1"
    resp.headers["X-Request-ID"] = request_id
    return resp

app.add_exception_handler(Exception, global_exception_handler)

# Simple request logging (method, path, status)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "OPTIONS":
        logging.debug("OPTIONS preflight", extra={"path": request.url.path, "origin": request.headers.get("origin")})
    response = await call_next(request)
    logging.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response

from routes import debug_db as debug_db_route
app.include_router(debug_db_route.router)

# Optional debug helper to verify auth in environments where DEBUG_AUTH=true
from fastapi import Depends
from routes.deps import get_current_user

debug_router = APIRouter()


@debug_router.get("/debug/whoami")
def whoami(user=Depends(get_current_user)):
    return {"user_id": user.id}

if DEBUG_AUTH:
    app.include_router(debug_router)

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

# Expose onboarding routes also without the /api prefix to match legacy/front-end callers.
app.include_router(onboarding_route.router)
app.include_router(analytics_route.router)

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

ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
if ENABLE_SCHEDULER:
    scheduler = BackgroundScheduler()
    def job():
        with Session(engine) as s:
            run_sweep(s, persona="teacher")
    scheduler.add_job(job, "interval", minutes=15)
    scheduler.start()
else:
    logger.info("[startup] Scheduler disabled (ENABLE_SCHEDULER=false)")

# >>> SEED EXERCISES START
from seed.exercises_intro_python import seed_intro_python_exercises

ENABLE_STARTUP_SEED = os.getenv("ENABLE_STARTUP_SEED", "false").lower() == "true"
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

@app.on_event("startup")
def seed_intro_python():
    if not ENABLE_STARTUP_SEED:
        logger.info("[startup] Skipping seed_intro_python (ENABLE_STARTUP_SEED=false)")
        return
    logger.info("[startup] Seeding intro python exercises...")
    with Session(engine) as session:
        seed_intro_python_exercises(session)
# --- debug: log key API routes at startup so we know they are mounted in prod ---
@app.on_event("startup")
def log_key_routes():
    logger = logging.getLogger("startup.routes")
    routes = []
    for r in app.router.routes:
        methods = getattr(r, "methods", None) or []
        for m in methods:
            routes.append(f"{m} {r.path}")
    logger.warning("Mounted routes (%d): %s", len(routes), sorted(set(routes)))
# <<< SEED EXERCISES END

# Backward compatibility: allow legacy clients hitting /tasks/upcoming without /api prefix
from routes.tasks import list_upcoming as list_upcoming_tasks  # type: ignore

@app.get("/tasks/upcoming", include_in_schema=False)
def upcoming_compat(session: Session = Depends(get_session)):
    return list_upcoming_tasks(session=session)
