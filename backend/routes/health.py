from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}


@router.get("/api/debug/cors")
def debug_cors(request: Request):
    return {
        "ok": True,
        "origin": request.headers.get("origin"),
        "host": request.headers.get("host"),
        "allowed_origins": getattr(request.app.state, "allowed_origins", None) or [],
    }
