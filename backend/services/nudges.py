# >>> PERSONA START
from __future__ import annotations

import random
from typing import Dict, Any, Literal
from datetime import datetime, timezone


Mood = Literal[
    "mood_calm_v1",
    "mood_snark_v1",
    "mood_disappointed_v1",
    "mood_intervention_v1",
    "mood_done_v1",
]


def pick_emoji(cfg: Dict[str, Any]) -> dict:
    emoji_set = cfg.get("ui", {}).get("emojiSet", [])
    max_count = int(cfg.get("ui", {}).get("emojiMax", 1))
    sample = random.sample(emoji_set, k=min(max_count, len(emoji_set))) if emoji_set else []
    return {
        "e1": sample[0] if sample else "",
        "eFrog": "🐸" if "🐸" in emoji_set else (sample[0] if sample else ""),
    }


def choose_bucket(minutes_to_due: int, overdue: bool, repeated_deferrals: int) -> Mood:
    if overdue:
        return "mood_intervention_v1"
    if minutes_to_due > 1440:
        return "mood_calm_v1"
    if 60 < minutes_to_due <= 1440:
        return "mood_snark_v1" if repeated_deferrals >= 2 else "mood_calm_v1"
    if 0 < minutes_to_due <= 60:
        return "mood_disappointed_v1" if repeated_deferrals >= 1 else "mood_snark_v1"
    return "mood_done_v1"


def render_micro(persona_cfg: Dict[str, Any], phase: str) -> str:
    scripts = persona_cfg.get("microScripts", {})
    lines = scripts.get(phase, []) or scripts.get("preTask", [])
    if not lines:
        return ""
    tokens = pick_emoji(persona_cfg)
    line = random.choice(lines)
    return line.replace("{{e1}}", tokens["e1"]).replace("{{eFrog}}", tokens["eFrog"]).strip()


def generate_nudge(persona_cfg: Dict[str, Any], phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": render_micro(persona_cfg, phase),
        "persona": persona_cfg.get("displayName"),
        "color": persona_cfg.get("ui", {}).get("color"),
        "phase": phase,
        "meta": {
            "taskId": context.get("taskId"),
            "dueAt": context.get("dueAt"),
            "now": datetime.now(timezone.utc).isoformat(),
        },
    }


# >>> PERS-WARM START
_SUBTYPE_LINES = {
    "near_miss": {
        "calm": "So close yesterday — lock it in 🌿",
        "snark": "Nearly there last time. Finish the arc 😏",
    },
    "sign": {
        "calm": "Watch the sign; same magnitude, flipped.",
        "snark": "Minus signs: the silent boss battle.",
    },
    "unit": {
        "calm": "Unit check first, answer second.",
        "snark": "kN ≠ N. Choose your fighter.",
    },
    "recall": {
        "calm": "Quick retrieval, then we cruise.",
        "snark": "Brains love spaced snacks. Take a bite.",
    },
}


def persona_line_for_subtype(subtype: str, mood_code: str) -> str:
    mood = "calm"
    if mood_code and "snark" in mood_code:
        mood = "snark"
    bank = _SUBTYPE_LINES.get(subtype or "recall", _SUBTYPE_LINES["recall"])
    return bank.get(mood, bank["calm"])
# <<< PERS-WARM END
# <<< PERSONA END
