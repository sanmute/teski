# >>> DFE START
from __future__ import annotations

import math
from typing import Any, Dict

_ALLOWED_NAMES = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
_ALLOWED_NAMES.update({"abs": abs, "min": min, "max": max, "round": round})


def _compile_expr(expr: str):
    try:
        return compile(expr, "<formula>", "eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression: {expr}") from exc


def _validate_names(code, values: Dict[str, Any]) -> None:
    for name in code.co_names:
        if name not in values and name not in _ALLOWED_NAMES:
            raise ValueError(f"Illegal name in formula: {name}")


def eval_numeric_formula(expr: str, values: Dict[str, Any]) -> float:
    """Evaluate numeric formula with restricted globals."""

    code = _compile_expr(expr)
    _validate_names(code, values)
    result = eval(code, {"__builtins__": {}}, {**_ALLOWED_NAMES, **values})
    return float(result)


def eval_predicate(expr: str, values: Dict[str, Any]) -> bool:
    """Evaluate boolean constraint expression safely."""

    code = _compile_expr(expr)
    _validate_names(code, values)
    result = eval(code, {"__builtins__": {}}, {**_ALLOWED_NAMES, **values})
    if not isinstance(result, (bool, int, float)):
        raise ValueError("Constraint did not evaluate to a boolean-compatible value")
    return bool(result)
# <<< DFE END
