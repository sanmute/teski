from fastapi import APIRouter, Request
import settings

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}


@router.get("/health/auth")
def health_auth():
    debug_enabled = getenv("TESKI_DEBUG", "0") == "1"
    if not debug_enabled:
        raise HTTPException(status_code=404, detail="not_found")
    secret_present = bool(settings.SECRET_KEY)
    return {
        "algorithm": settings.ALGORITHM,
        "secret_present": secret_present,
        "secret_length": len(settings.SECRET_KEY or ""),
        "token_sub_type_expected": "int",  # current DB user id is int
    }


@router.get("/api/debug/cors")
def debug_cors(request: Request):
    return {
        "ok": True,
        "origin": request.headers.get("origin"),
        "host": request.headers.get("host"),
        "allowed_origins": getattr(request.app.state, "allowed_origins", None) or [],
    }
