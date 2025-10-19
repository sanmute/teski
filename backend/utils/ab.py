# >>> ABTEST START
import hashlib


def ab_bucket(user_id: int, experiment_code: str, splits: tuple[int, int] = (50, 50)) -> str:
    a, b = splits
    total = a + b
    if total <= 0:
        return "A"
    digest = hashlib.sha256(f"{experiment_code}:{user_id}".encode()).hexdigest()[:8]
    slot = int(digest, 16) % total
    return "A" if slot < a else "B"
# <<< ABTEST END
