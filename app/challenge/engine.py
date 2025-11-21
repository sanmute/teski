from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlmodel import Session, select

from app.data.mock_exercises import MOCK_EXERCISES
from app.exercises import Exercise, load_exercises
from app.behavioral.model import get_behavior_profile
from app.mastery.models import Skill, UserSkillMastery
from app.mastery.service import get_mastery_record, get_or_create_skill
from app.models import AnalyticsEvent, BehavioralProfile, Mistake, MemoryItem

DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 5
RECENT_WINDOW = 40
RECENT_COOLDOWN_IDS = 5
REVIEW_RATIO_STRUGGLE = 0.5
REVIEW_RATIO_NORMAL = 0.25
NEAR_TERM_WINDOW_DAYS = 2


class DifficultyBand(str, Enum):
    COMFORT = "comfort"
    CHALLENGE = "challenge"
    STRETCH = "stretch"


@dataclass(frozen=True)
class ChallengePolicy:
    comfort_ratio: float = 0.6
    challenge_ratio: float = 0.3
    stretch_ratio: float = 0.1
    review_ratio: float = 0.4
    max_stretch_per_run: int = 2


DEFAULT_CHALLENGE_POLICY = ChallengePolicy()


@dataclass(frozen=True)
class ExerciseCandidate:
    id: str
    concept: str
    difficulty: int
    type: str
    skill_name: str
    source: str  # "content" | "mock"
    keywords: Tuple[str, ...]

    @property
    def skill_key(self) -> str:
        return _normalize(self.skill_name)


@dataclass
class PlannedExercise:
    candidate: ExerciseCandidate
    is_review: bool
    reason: str

    @property
    def difficulty(self) -> int:
        return self.candidate.difficulty

    @property
    def exercise_id(self) -> str:
        return self.candidate.id


@dataclass
class PerformanceSnapshot:
    attempts: int
    correct_rate: float
    current_streak: int
    average_difficulty: float
    recent_ids: List[str]


@dataclass
class SessionPlan:
    skill: Skill
    mastery: float
    target_band: Tuple[int, int]
    review_items: List[PlannedExercise]
    challenge_items: List[PlannedExercise]
    ordered_items: List[PlannedExercise]
    performance: PerformanceSnapshot


_CONCEPT_SKILL_MAP: Dict[str, str] = {}


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _difficulty_label(value: int) -> str:
    if value <= 2:
        return "Easy"
    if value == 3:
        return "Medium"
    return "Hard"


def _primary_skill_name(exercise: Exercise) -> str:
    if isinstance(exercise.meta, dict):
        skill_hint = exercise.meta.get("skill")
        if isinstance(skill_hint, str) and skill_hint.strip():
            return skill_hint.strip()
    keywords = list(exercise.keywords or [])
    if keywords:
        return keywords[0]
    return exercise.concept


def _primary_skill_name_from_mock(mock: Dict[str, object]) -> str:
    skill_hint = mock.get("skill")
    if isinstance(skill_hint, str) and skill_hint.strip():
        return skill_hint.strip()
    tags = mock.get("tags") or []
    if isinstance(tags, Sequence) and tags:
        first = str(tags[0]).strip()
        if first:
            return first
    concept = mock.get("concept")
    return str(concept) if concept else "General"


@lru_cache()
def _candidate_map() -> Dict[str, ExerciseCandidate]:
    global _CONCEPT_SKILL_MAP
    _CONCEPT_SKILL_MAP = {}
    candidates: Dict[str, ExerciseCandidate] = {}
    for exercise in load_exercises():
        skill_name = _primary_skill_name(exercise)
        candidate = ExerciseCandidate(
            id=exercise.id,
            concept=exercise.concept,
            difficulty=max(DIFFICULTY_MIN, min(DIFFICULTY_MAX, int(exercise.difficulty or 1))),
            type=exercise.type.upper(),
            skill_name=skill_name,
            source="content",
            keywords=tuple(exercise.keywords or []),
        )
        candidates[candidate.id] = candidate
        _CONCEPT_SKILL_MAP[_normalize(exercise.concept)] = candidate.skill_name
    for mock in MOCK_EXERCISES:
        skill_name = _primary_skill_name_from_mock(mock)
        candidate = ExerciseCandidate(
            id=str(mock["id"]),
            concept=str(mock["concept"]),
            difficulty=max(DIFFICULTY_MIN, min(DIFFICULTY_MAX, int(mock.get("difficulty", 1)))),
            type=str(mock["type"]).upper(),
            skill_name=skill_name,
            source="mock",
            keywords=tuple(mock.get("tags", []) or []),
        )
        candidates[candidate.id] = candidate
        _CONCEPT_SKILL_MAP[_normalize(candidate.concept)] = candidate.skill_name
    return candidates


def _concept_to_skill_name(concept: str) -> str:
    key = _normalize(concept)
    return _CONCEPT_SKILL_MAP.get(key, concept.strip())


def get_candidate(exercise_id: str) -> Optional[ExerciseCandidate]:
    return _candidate_map().get(exercise_id)


def derive_skill_name_for_exercise(exercise: Exercise) -> str:
    """Shared helper to keep skill attribution consistent with challenge engine."""
    skill_name = _primary_skill_name(exercise)
    return skill_name or exercise.concept


def derive_skill_name_for_concept(concept: str) -> str:
    return _concept_to_skill_name(concept)


def _candidates_for_skill(skill_key: str) -> List[ExerciseCandidate]:
    return [cand for cand in _candidate_map().values() if cand.skill_key == skill_key]


def _candidates_by_concept(concept: str) -> List[ExerciseCandidate]:
    key = _normalize(concept)
    return [cand for cand in _candidate_map().values() if _normalize(cand.concept) == key]


def _difficulty_band_for_mastery(value: float) -> Tuple[int, int]:
    if value < 30:
        return 1, 2
    if value < 60:
        return 2, 3
    if value < 80:
        return 3, 4
    return 4, 5


def classify_exercise_band(mastery_level: float, exercise_difficulty: int) -> DifficultyBand:
    """Map mastery (0-100) and difficulty (1-5) to a comfort/challenge/stretch bucket."""
    comfort_low, comfort_high = _difficulty_band_for_mastery(mastery_level)
    if exercise_difficulty <= comfort_high and exercise_difficulty >= comfort_low:
        return DifficultyBand.COMFORT
    if exercise_difficulty == comfort_high + 1:
        return DifficultyBand.CHALLENGE
    return DifficultyBand.STRETCH


def derive_policy(base: ChallengePolicy, behavior: Optional[BehavioralProfile]) -> ChallengePolicy:
    if not behavior:
        return base
    comfort = base.comfort_ratio
    challenge = base.challenge_ratio
    stretch = base.stretch_ratio
    review_ratio = base.review_ratio
    if getattr(behavior, "challenge_preference", 50) >= 70:
        comfort -= 0.1
        challenge += 0.05
        stretch += 0.05
    elif getattr(behavior, "challenge_preference", 50) <= 30 or getattr(behavior, "fatigue_risk", 0) >= 70:
        comfort += 0.1
        challenge -= 0.05
        stretch = max(0.05, stretch - 0.05)
    if getattr(behavior, "fatigue_risk", 0) >= 70:
        review_ratio = max(0.3, review_ratio - 0.1)
    # normalize comfort+challenge+stretch to 1
    total = comfort + challenge + stretch
    comfort, challenge, stretch = (comfort / total, challenge / total, stretch / total)
    return ChallengePolicy(
        comfort_ratio=comfort,
        challenge_ratio=challenge,
        stretch_ratio=stretch,
        review_ratio=review_ratio,
        max_stretch_per_run=base.max_stretch_per_run,
    )


def compute_recent_performance(session: Session, user_id: UUID, skill: Skill) -> PerformanceSnapshot:
    events = session.exec(
        select(AnalyticsEvent)
        .where(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.kind.in_(("exercise_correct", "exercise_incorrect")),
        )
        .order_by(AnalyticsEvent.ts.desc())
        .limit(RECENT_WINDOW)
    ).all()
    skill_key = _normalize(skill.name)
    attempts = 0
    correct = 0
    streak = 0
    total_difficulty = 0
    recent_ids: List[str] = []
    for event in events:
        exercise_id = None
        payload = event.payload or {}
        if isinstance(payload, dict):
            exercise_id = payload.get("exercise_id")
        if not exercise_id:
            continue
        candidate = get_candidate(str(exercise_id))
        if not candidate or candidate.skill_key != skill_key:
            continue
        attempts += 1
        correct_flag = event.kind == "exercise_correct"
        if correct_flag:
            correct += 1
            streak = streak + 1 if attempts == len(recent_ids) + 1 else streak + 1
        else:
            streak = 0
        total_difficulty += candidate.difficulty
        recent_ids.append(candidate.id)
    if attempts == 0:
        return PerformanceSnapshot(
            attempts=0,
            correct_rate=0.0,
            current_streak=0,
            average_difficulty=0.0,
            recent_ids=[],
        )
    correct_rate = correct / attempts if attempts else 0.0
    average_difficulty = total_difficulty / attempts if attempts else 0.0
    return PerformanceSnapshot(
        attempts=attempts,
        correct_rate=correct_rate,
        current_streak=streak,
        average_difficulty=average_difficulty,
        recent_ids=recent_ids[:RECENT_COOLDOWN_IDS],
    )


def _recent_exercise_ids(performance: PerformanceSnapshot) -> List[str]:
    return performance.recent_ids[:RECENT_COOLDOWN_IDS]


def _adjust_band(base: Tuple[int, int], performance: PerformanceSnapshot) -> Tuple[int, int]:
    low, high = base
    if performance.attempts >= 5 and performance.correct_rate > 0.85 and performance.current_streak >= 5:
        high = min(DIFFICULTY_MAX, high + 1)
        low = min(high - 1, max(DIFFICULTY_MIN, low + 1))
    elif performance.attempts >= 10 and performance.correct_rate < 0.5:
        low = max(DIFFICULTY_MIN, low - 1)
        high = max(low + 1, high - 1)
    return low, high


def _needs_easy_win(performance: PerformanceSnapshot) -> bool:
    return performance.attempts >= 5 and performance.correct_rate < 0.3


def _review_target(performance: PerformanceSnapshot, length: int) -> int:
    if performance.attempts >= 10 and performance.correct_rate < 0.5:
        ratio = REVIEW_RATIO_STRUGGLE
    else:
        ratio = REVIEW_RATIO_NORMAL
    return max(1, int(round(length * ratio)))


def get_due_mistake_exercises(
    session: Session,
    user_id: UUID,
    skill: Skill,
    limit: int,
) -> List[ExerciseCandidate]:
    if limit <= 0:
        return []
    skill_key = _normalize(skill.name)
    seen: set[str] = set()
    due: List[ExerciseCandidate] = []
    now = datetime.utcnow()
    near_term = now + timedelta(days=NEAR_TERM_WINDOW_DAYS)

    memory_stmt = (
        select(MemoryItem)
        .where(MemoryItem.user_id == user_id)
        .order_by(MemoryItem.due_at.asc())
        .limit(200)
    )
    for memory in session.exec(memory_stmt):
        if memory.due_at and memory.due_at > near_term:
            continue
        concept_skill = _normalize(_concept_to_skill_name(memory.concept))
        if concept_skill != skill_key:
            continue
        for candidate in _candidates_by_concept(memory.concept):
            if candidate.id in seen:
                continue
            due.append(candidate)
            seen.add(candidate.id)
            if len(due) >= limit:
                return due

    mistake_stmt = (
        select(Mistake)
        .where(Mistake.user_id == user_id)
        .order_by(Mistake.created_at.desc())
        .limit(200)
    )
    mistakes = [m for m in session.exec(mistake_stmt) if _normalize(_concept_to_skill_name(m.concept)) == skill_key]
    freq_by_subtype: Counter[str] = Counter()
    for mistake in mistakes:
        if mistake.subtype:
            subtype = str(mistake.subtype).split(":", 1)[-1]
            freq_by_subtype[subtype] += 1

    sorted_mistakes = sorted(
        mistakes,
        key=lambda m: (
            -freq_by_subtype.get(str(m.subtype).split(":", 1)[-1], 0),
            m.created_at,
        ),
        reverse=True,
    )

    for mistake in sorted_mistakes:
        for candidate in _candidates_by_concept(mistake.concept):
            if candidate.id in seen:
                continue
            due.append(candidate)
            seen.add(candidate.id)
            if len(due) >= limit:
                return due
    return due


def _sort_candidates_by_target(
    candidates: Iterable[ExerciseCandidate],
    target_low: int,
    target_high: int,
    prefer_harder: bool,
) -> List[ExerciseCandidate]:
    center = target_high if prefer_harder else (target_low + target_high) / 2

    def score(candidate: ExerciseCandidate) -> Tuple[float, int, str]:
        return (
            abs(candidate.difficulty - center),
            -candidate.difficulty if prefer_harder else candidate.difficulty,
            candidate.id,
        )

    return sorted(candidates, key=score)


def _pick_new_candidates(
    skill_key: str,
    count: int,
    avoid_ids: set[str],
    target_low: int,
    target_high: int,
    prefer_harder: bool,
) -> List[ExerciseCandidate]:
    if count <= 0:
        return []
    pool = [cand for cand in _candidates_for_skill(skill_key) if cand.id not in avoid_ids]
    if not pool:
        pool = [cand for cand in _candidate_map().values() if cand.id not in avoid_ids]
    ordered = _sort_candidates_by_target(pool, target_low, target_high, prefer_harder)
    return ordered[:count]


def _ensure_easy_win(
    ordered: List[PlannedExercise],
    target_low: int,
) -> List[PlannedExercise]:
    if not ordered:
        return ordered
    if ordered[0].difficulty <= target_low:
        return ordered
    for idx in range(1, len(ordered)):
        if ordered[idx].difficulty <= target_low:
            ordered.insert(0, ordered.pop(idx))
            break
    return ordered


def _enforce_hard_guard(
    ordered: List[PlannedExercise],
    hard_threshold: int,
) -> List[PlannedExercise]:
    hard_run = 0
    for idx in range(len(ordered)):
        difficulty = ordered[idx].difficulty
        if difficulty >= hard_threshold:
            hard_run += 1
        else:
            hard_run = 0
        if hard_run <= 2:
            continue
        swap_idx = None
        for future in range(idx + 1, len(ordered)):
            if ordered[future].difficulty < hard_threshold:
                swap_idx = future
                break
        if swap_idx is None:
            break
        candidate = ordered.pop(swap_idx)
        ordered.insert(idx, candidate)
        hard_run = 1
    return ordered


def _band_targets(pool_size: int, policy: ChallengePolicy) -> Dict[DifficultyBand, int]:
    n_comfort = int(round(pool_size * policy.comfort_ratio))
    n_challenge = int(round(pool_size * policy.challenge_ratio))
    n_stretch = pool_size - n_comfort - n_challenge
    if n_stretch > policy.max_stretch_per_run:
        n_stretch = policy.max_stretch_per_run
    while n_comfort + n_challenge + n_stretch < pool_size:
        n_comfort += 1
    return {
        DifficultyBand.COMFORT: max(0, n_comfort),
        DifficultyBand.CHALLENGE: max(0, n_challenge),
        DifficultyBand.STRETCH: max(0, n_stretch),
    }


def _allocate_by_band(
    candidates: List[ExerciseCandidate],
    targets: Dict[DifficultyBand, int],
    mastery: float,
    is_review: bool,
) -> List[PlannedExercise]:
    bucketed: Dict[DifficultyBand, List[ExerciseCandidate]] = {
        DifficultyBand.COMFORT: [],
        DifficultyBand.CHALLENGE: [],
        DifficultyBand.STRETCH: [],
    }
    for cand in candidates:
        band = classify_exercise_band(mastery, cand.difficulty)
        bucketed[band].append(cand)

    ordered_candidates: List[ExerciseCandidate] = []
    for band in (DifficultyBand.COMFORT, DifficultyBand.CHALLENGE, DifficultyBand.STRETCH):
        need = targets.get(band, 0)
        if need <= 0:
            continue
        bucket = bucketed.get(band, [])
        take = bucket[:need]
        ordered_candidates.extend(take)
        if len(take) < need:
            spill_needed = need - len(take)
            if band == DifficultyBand.CHALLENGE:
                spill = bucketed[DifficultyBand.COMFORT][:spill_needed]
                ordered_candidates.extend(spill)
            elif band == DifficultyBand.STRETCH:
                spill = bucketed[DifficultyBand.CHALLENGE][:spill_needed]
                if len(spill) < spill_needed:
                    spill += bucketed[DifficultyBand.COMFORT][: spill_needed - len(spill)]
                ordered_candidates.extend(spill)

    seen: set[str] = set()
    planned: List[PlannedExercise] = []
    for cand in ordered_candidates:
        if cand.id in seen:
            continue
        seen.add(cand.id)
        planned.append(PlannedExercise(candidate=cand, is_review=is_review, reason="due_review" if is_review else "new_challenge"))
    return planned


def _pick_skill_for_user(session: Session, user_id: UUID) -> Skill:
    mastery_row = session.exec(
        select(UserSkillMastery).where(UserSkillMastery.user_id == user_id).order_by(UserSkillMastery.mastery.asc())
    ).first()
    if mastery_row:
        skill = session.get(Skill, mastery_row.skill_id)
        if skill:
            return skill
    # fallback to the first available candidate skill
    for candidate in _candidate_map().values():
        return get_or_create_skill(session, candidate.skill_name)
    return get_or_create_skill(session, "General Skill")


def select_exercises_for_session(
    session: Session,
    user_id: UUID,
    *,
    skill_id: Optional[UUID] = None,
    length: int = 3,
    behavior_profile: Optional[BehavioralProfile] = None,
) -> SessionPlan:
    length = max(1, min(10, length))
    if skill_id:
        skill = session.get(Skill, skill_id)
        if not skill:
            raise ValueError("skill_not_found")
    else:
        skill = _pick_skill_for_user(session, user_id)

    behavior = behavior_profile or get_behavior_profile(session, user_id)
    policy = derive_policy(DEFAULT_CHALLENGE_POLICY, behavior)
    mastery_record = get_mastery_record(session, user_id, skill.id)
    base_band = _difficulty_band_for_mastery(mastery_record.mastery)
    performance = compute_recent_performance(session, user_id, skill)
    adjusted_band = _adjust_band(base_band, performance)
    target_low, target_high = adjusted_band

    total_items = length
    review_target = min(total_items, int(round(total_items * policy.review_ratio)))
    recent_ids = set(_recent_exercise_ids(performance))

    review_candidates = get_due_mistake_exercises(session, user_id, skill, review_target * 2)
    avoid_ids: set[str] = set(recent_ids)
    for candidate in review_candidates:
        avoid_ids.add(candidate.id)

    prefer_harder = performance.correct_rate > 0.85 and performance.current_streak >= 5
    if behavior:
        if behavior.fatigue_risk >= 70:
            prefer_harder = False
        elif behavior.challenge_preference >= 70:
            prefer_harder = True
        elif behavior.challenge_preference <= 30:
            prefer_harder = False

    new_needed = max(0, total_items - review_target)
    # pull a slightly larger pool to allow band allocation
    challenge_candidates = _pick_new_candidates(
        _normalize(skill.name),
        max(new_needed + 2, total_items),
        avoid_ids,
        target_low,
        target_high,
        prefer_harder,
    )

    review_targets = _band_targets(review_target, policy)
    new_targets = _band_targets(new_needed, policy)

    review_items = _allocate_by_band(review_candidates, review_targets, mastery_record.mastery, is_review=True)
    challenge_items = _allocate_by_band(challenge_candidates, new_targets, mastery_record.mastery, is_review=False)

    # interleave review and new
    ordered: List[PlannedExercise] = []
    ri, ci = 0, 0
    while len(ordered) < total_items and (ri < len(review_items) or ci < len(challenge_items)):
        if ri < len(review_items):
            ordered.append(review_items[ri])
            ri += 1
        if len(ordered) >= total_items:
            break
        if ci < len(challenge_items):
            ordered.append(challenge_items[ci])
            ci += 1

    ordered = ordered[:total_items]
    hard_threshold = max(target_high, 4)
    ordered = _enforce_hard_guard(ordered, hard_threshold)
    if _needs_easy_win(performance):
        ordered = _ensure_easy_win(ordered, target_low)

    return SessionPlan(
        skill=skill,
        mastery=mastery_record.mastery,
        target_band=adjusted_band,
        review_items=review_items,
        challenge_items=challenge_items,
        ordered_items=ordered,
        performance=performance,
    )


def plan_to_response_items(plan: SessionPlan) -> List[dict]:
    items: List[dict] = []
    for idx, entry in enumerate(plan.ordered_items):
        candidate = entry.candidate
        items.append(
            {
                "order": idx,
                "exercise_id": candidate.id,
                "concept": candidate.concept,
                "difficulty": candidate.difficulty,
                "difficulty_label": _difficulty_label(candidate.difficulty),
                "is_review": entry.is_review,
                "skill_id": str(plan.skill.id),
                "skill_name": plan.skill.name,
                "source": "review" if entry.is_review else "challenge",
            }
        )
    return items
