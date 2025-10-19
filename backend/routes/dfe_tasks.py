# >>> DFE START
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.db import get_session
from backend.routes.deps import get_current_user
from backend.schemas_dfe_tasks import (
    AttemptResult,
    SkillNodeCreate,
    SubmitAnswer,
    TaskInstanceOut,
    TaskTemplateCreate,
)
from backend.services.dfe_tasks import (
    create_template,
    get_or_create_skill,
    grade_and_update_with_memory_v1,
    instantiate_for_user,
)

router = APIRouter(prefix="/api/v1/tasks", tags=["dfe"])


@router.post("/skills", response_model=dict)
def create_skill_endpoint(
    payload: SkillNodeCreate,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> dict:
    """Create a new skill node for the parametric exercise graph.

    Example request::
        {
          "key": "math.integrals.substitution",
          "title": "Integral Substitution",
          "graph_version": "v1"
        }

    Example response::
        {"id": 1, "key": "math.integrals.substitution", "graph_version": "v1"}
    """

    skill = get_or_create_skill(session, payload.key, payload.title, payload.graph_version)
    return {"id": skill.id, "key": skill.key, "graph_version": skill.graph_version}


@router.post("/templates", response_model=dict)
def create_template_endpoint(
    payload: TaskTemplateCreate,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> dict:
    """Register a parametric task template tied to a skill.

    Example request::
        {
          "code": "phys.accel.01",
          "title": "Acceleration",
          "skill_key": "physics.kinematics.acceleration",
          "task_type": "numeric",
          "text_template": "A car accelerates from {{v0}} to {{v1}} in {{t}} s. Compute a.",
          "parameters": {"v0": [0, 5, 10], "v1": [15, 20, 25], "t": [3, 4, 5]},
          "constraints": {"expr": "v1 > v0 and t != 0"},
          "answer_spec": {"formula": "(v1 - v0)/t", "tolerance": 1e-6}
        }

    Example response::
        {"id": 1, "code": "phys.accel.01"}
    """

    template = create_template(session, payload)
    return {"id": template.id, "code": template.code}


@router.post("/instantiate/{template_code}", response_model=TaskInstanceOut)
def instantiate_endpoint(
    template_code: str,
    force_new: bool = False,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> TaskInstanceOut:
    """Generate or fetch a deterministic task instance for the current user.

    Example response::
        {
          "instance_id": 1,
          "template_code": "phys.accel.01",
          "text": "A car accelerates from 0 to 20 in 4 s. Compute a.",
          "params": {"v0": 0, "v1": 20, "t": 4},
          "task_type": "numeric"
        }
    """

    instance, template = instantiate_for_user(session, template_code, user.id, force_new=force_new)
    return TaskInstanceOut(
        instance_id=instance.id,
        template_code=template.code,
        text=instance.rendered_text,
        params=instance.params,
        task_type=template.task_type.value,
    )


@router.post("/submit/{instance_id}", response_model=AttemptResult)
def submit_answer_endpoint(
    instance_id: int,
    payload: SubmitAnswer,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> AttemptResult:
    """Submit an answer for grading and update mastery scores.

    Example request::
        {"answer": 5.0, "latency_ms": 1234}

    Example response::
        {"correct": true, "mastery_after": 0.2}
    """

    correct, mastery = grade_and_update_with_memory_v1(session, instance_id, user.id, payload.answer, payload.latency_ms)
    return AttemptResult(correct=correct, mastery_after=mastery)
# <<< DFE END
