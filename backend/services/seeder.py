# filepath: /Users/santerimutanen/Documents/teski/backend/services/seeder.py
from pathlib import Path
import json
from datetime import datetime
from sqlmodel import Session
from models import Task

def load_seed(session: Session) -> int:
    from sqlmodel import select
    from models import Task
    import json
    from datetime import datetime
    from pathlib import Path

    tasks_file = Path(__file__).parent.parent / "seed" / "tasks.json"
    with tasks_file.open("r", encoding="utf-8") as f:
        tasks = json.load(f)

    count = 0
    for task_data in tasks:
        # Convert due_iso from string to datetime
        task_data["due_iso"] = datetime.fromisoformat(task_data["due_iso"].replace("Z", "+00:00"))

        # Check if the task already exists
        existing_task = session.exec(select(Task).where(Task.id == task_data["id"])).first()
        if existing_task:
            continue  # Skip if the task already exists

        task = Task(**task_data)
        session.add(task)
        count += 1

    session.commit()
    return count
