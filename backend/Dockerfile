FROM python:3.12.12 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Create venv and install dependencies
RUN python -m venv /app/.venv
COPY requirements.txt ./
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime image ----
FROM python:3.12.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Put the venv first on PATH so "python" and packages resolve cleanly
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy app code
COPY . .

# Fly will route to internal_port = 8080 (per fly.toml)
EXPOSE 8080

# IMPORTANT: run uvicorn as a Python module (no reliance on uvicorn console script)
# Adjust "app.main:app" if your FastAPI instance lives elsewhere (e.g. "main:app")
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
