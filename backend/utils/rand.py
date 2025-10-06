# >>> DFE START
from __future__ import annotations

import hashlib
import hmac
import random
from typing import Any, Dict


def deterministic_seed(user_id: int, template_code: str, salt: str) -> int:
    """HMAC-based deterministic seed for per-user template sampling."""

    key = salt.encode("utf-8")
    msg = f"{user_id}:{template_code}".encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    return int.from_bytes(digest[:8], "big")


def sample_params(params_domain: Dict[str, Any], rnd: random.Random) -> Dict[str, Any]:
    """Sample parameters from domain definition using provided RNG."""

    sampled: Dict[str, Any] = {}
    for name, domain in params_domain.items():
        if isinstance(domain, list):
            if not domain:
                raise ValueError(f"Empty domain for parameter {name}")
            sampled[name] = rnd.choice(domain)
            continue
        if isinstance(domain, dict) and "range" in domain:
            start, stop = domain["range"]
            step = domain.get("step")
            if step:
                if step <= 0:
                    raise ValueError(f"Non-positive step for parameter {name}")
                span = int(round((stop - start) / step))
                sampled[name] = start + rnd.randrange(0, span + 1) * step
            else:
                sampled[name] = rnd.uniform(start, stop)
            continue
        sampled[name] = domain
    return sampled
# <<< DFE END
