from __future__ import annotations

import os

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
