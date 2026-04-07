FROM python:3.11-slim

LABEL maintainer="workflow-eval-env"
LABEL org.opencontainers.image.title="OpenEnv Workflow Evaluation Environment"
LABEL tags="openenv"

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies with specific timeout
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements-prod.txt

# Copy project
COPY . .

# Expose port for HuggingFace Spaces (7860) and general use (8000)
EXPOSE 7860
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "from models import Observation; print('OK')" || exit 1

# Run FastAPI server for HuggingFace Space deployment
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
