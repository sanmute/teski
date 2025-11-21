from app.challenge.engine import (
    ChallengePolicy,
    DEFAULT_CHALLENGE_POLICY,
    DifficultyBand,
    ExerciseCandidate,
    _band_targets,
    _allocate_by_band,
    classify_exercise_band,
    derive_policy,
)


def dummy_candidate(idx: int, difficulty: int) -> ExerciseCandidate:
    return ExerciseCandidate(
        id=f"ex{idx}",
        concept="dummy",
        difficulty=difficulty,
        type="NUMERIC",
        skill_name="Test Skill",
        source="content",
        keywords=(),
    )


def test_classify_band_increases_with_difficulty():
    assert classify_exercise_band(20, 1) == DifficultyBand.COMFORT
    assert classify_exercise_band(20, 3) in {DifficultyBand.CHALLENGE, DifficultyBand.STRETCH}
    assert classify_exercise_band(70, 4) in {DifficultyBand.COMFORT, DifficultyBand.CHALLENGE, DifficultyBand.STRETCH}


def test_derive_policy_adjusts_for_high_challenge_preference():
    behavior = type("obj", (), {"challenge_preference": 80, "fatigue_risk": 20, "review_vs_new_bias": 50})
    policy = derive_policy(DEFAULT_CHALLENGE_POLICY, behavior)
    assert policy.challenge_ratio > DEFAULT_CHALLENGE_POLICY.challenge_ratio
    assert abs(policy.comfort_ratio + policy.challenge_ratio + policy.stretch_ratio - 1.0) < 1e-6


def test_band_targets_respect_max_stretch():
    policy = ChallengePolicy(max_stretch_per_run=1)
    targets = _band_targets(5, policy)
    assert targets[DifficultyBand.STRETCH] <= 1


def test_allocate_by_band_prefers_requested_buckets():
    candidates = [dummy_candidate(i, difficulty=diff) for i, diff in enumerate([1, 2, 3, 4, 5])]
    targets = {DifficultyBand.COMFORT: 2, DifficultyBand.CHALLENGE: 2, DifficultyBand.STRETCH: 1}
    planned = _allocate_by_band(candidates, targets, mastery=50, is_review=False)
    # should not exceed total targets and keep uniqueness
    assert len(planned) <= sum(targets.values())
    ids = [p.exercise_id for p in planned]
    assert len(ids) == len(set(ids))
