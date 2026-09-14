# ==========================================
# Base Stage: Install uv and dependencies
# ==========================================
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install system utilities and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY requirements.txt .

# Install dependencies into system Python using uv
RUN uv pip install --no-cache -r requirements.txt

COPY . .

# ==========================================
# Target 1: Router Cloud Run Service
# (GemCreator, Intake, Validation, Discovery)
# ==========================================
FROM base as router-service
EXPOSE 8000
CMD ["uvicorn", "router_main:app", "--host", "0.0.0.0", "--port", "8000"]

# ==========================================
# Target 2: Worker Cloud Run Job
# (Ephemeral Worker Execution Runner)
# ==========================================
FROM base as worker-job
CMD ["python", "worker_job_main.py"]