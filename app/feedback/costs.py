from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlmodel import Session, select, func

from .models import FeedbackEvent

EUR = float(os.getenv("EUR_MULTIPLIER", "1.0"))

PRICES_EUR = {
    "mini:gpt4_1": {"in": 0.15 * EUR, "out": 0.60 * EUR},
    "mini:haiku4_5": {"in": 0.10 * EUR, "out": 0.50 * EUR},
    "pro:gpt4_1": {"in": 5.00 * EUR, "out": 15.00 * EUR},
    "pro:sonnet3_7": {"in": 3.00 * EUR, "out": 15.00 * EUR},
    "local:llama70b": {"in": 0.00, "out": 0.00},
}


def estimate_cost_eur(model: str, tokens_in: int, tokens_out: int) -> float:
    prices = PRICES_EUR.get(model, {"in": 0.0, "out": 0.0})
    return (tokens_in / 1_000_000) * prices["in"] + (tokens_out / 1_000_000) * prices["out"]


def _scalar(value: Any) -> float:
    if isinstance(value, tuple):
        return value[0]
    return float(value or 0.0)


def get_cost_stats(session: Session) -> Dict[str, float | int]:
    """Aggregate feedback generation cost metrics for admin dashboards."""

    month_ago = datetime.utcnow() - timedelta(days=30)
    total_cost = _scalar(session.exec(select(func.sum(FeedbackEvent.cost_eur))).one())
    cost_30d = _scalar(
        session.exec(
            select(func.sum(FeedbackEvent.cost_eur)).where(FeedbackEvent.created_at >= month_ago)
        ).one()
    )
    total_events = _scalar(session.exec(select(func.count(FeedbackEvent.id))).one())
    total_hits = _scalar(
        session.exec(
            select(func.count(FeedbackEvent.id)).where(FeedbackEvent.cached_hit.is_(True))
        ).one()
    )
    hit_rate = float(total_hits) / float(total_events) if total_events else 0.0

    return {
        "cost_total_eur": float(total_cost),
        "cost_last_30d_eur": float(cost_30d),
        "events_total": int(total_events),
        "cache_hit_rate": hit_rate,
    }
