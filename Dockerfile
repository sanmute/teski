FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies (from backend/ — the deployed server)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the legacy backend source (main.py, routes/, services/, db.py, …)
COPY backend/ .

# Copy the root app/ module so backend/main.py can do `from app.* import …`
COPY app/ ./app/

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug", "--access-log"]
