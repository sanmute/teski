# services/notify.py
from sqlmodel import Session, select
from ..models_push import PushSubscription
from ..routes.push import send_web_push

def push_reminder(session: Session, user_id: str, task_id: str, title: str, body: str):
    subs = session.exec(select(PushSubscription).where(
        PushSubscription.user_id == user_id, PushSubscription.active == True
    )).all()
    payload = {
        "title": title,
        "body": body,
        "taskId": task_id,
        "collapseId": f"task-{task_id}",
    }
    sent = 0
    for s in subs:
        if send_web_push(s, payload): sent += 1
    session.commit()
    return sent
