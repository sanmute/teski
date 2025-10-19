from pathlib import Path
from dotenv import load_dotenv

BASE_PATH = Path(__file__).resolve().parent.parent
load_dotenv(BASE_PATH / ".env", override=False)
load_dotenv(BASE_PATH / ".env.backend", override=True)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routes import tasks as tasks_route
from .routes import reminders as reminders_route
from .routes import health as health_route
from .routes import studypack as studypack_route
from .db import init_db, get_session
from sqlmodel import Session
from .services.seeder import load_seed
from .schemas import MockLoadResp
from fastapi import APIRouter

init_db()
app = FastAPI(title="Deadline Agent Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes import debug_db as debug_db_route
app.include_router(debug_db_route.router)

# app/backend/main.py
from .routes import import_ics as import_ics_route
app.include_router(import_ics_route.router)

app.include_router(health_route.router)
app.include_router(tasks_route.router)
app.include_router(reminders_route.router)
app.include_router(studypack_route.router)

from .routes import integrations as integrations_route
app.include_router(integrations_route.router)

from .routes import users as users_route
app.include_router(users_route.router)

from .routes import estimates as estimates_route
app.include_router(estimates_route.router)

from .routes import topics as topics_route
app.include_router(topics_route.router)

from .routes import push as push_route
app.include_router(push_route.router)

# >>> PERSONA START
from .routes import persona as persona_route

app.include_router(persona_route.router)
# <<< PERSONA END

# >>> LEADERBOARD START MAIN ROUTER
from .routes import leaderboard as leaderboard_route

app.include_router(leaderboard_route.router)
# >>> LEADERBOARD END MAIN ROUTER

# >>> DFE START
from .routes import dfe_tasks as dfe_tasks_route

app.include_router(dfe_tasks_route.router)
# <<< DFE END

# >>> MEMORY START
from .routes import memory as memory_route

app.include_router(memory_route.router)
# <<< MEMORY END

# >>> MEMORY V1 START
from .routes import memory_v1 as memory_v1_route

app.include_router(memory_v1_route.router)
# <<< MEMORY V1 END

# mock loader for demo
misc = APIRouter(prefix="/api", tags=["misc"])

@misc.post("/tasks/mock-load", response_model=MockLoadResp)
def mock_load(session: Session = Depends(get_session)):
    loaded = load_seed(session)
    return MockLoadResp(loaded=loaded)

app.include_router(misc)

# in main.py
from apscheduler.schedulers.background import BackgroundScheduler
from .db import get_session, engine
from sqlmodel import Session
from .services.reminder_engine import run_sweep

scheduler = BackgroundScheduler()
def job():
    with Session(engine) as s:
        run_sweep(s, persona="teacher")
scheduler.add_job(job, "interval", minutes=15)
scheduler.start()
