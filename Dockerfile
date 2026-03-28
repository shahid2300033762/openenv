FROM python:3.11-slim

LABEL maintainer="workflow-eval-env"
LABEL org.opencontainers.image.title="OpenEnv Workflow Evaluation Environment"
LABEL tags="openenv"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port for HuggingFace Spaces (7860) and general use (8000)
EXPOSE 7860
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "from models import Observation; print('OK')" || exit 1

# Run FastAPI server for HuggingFace Space deployment
# Falls back to validation if server fails
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port 7860 || python main.py --validate"]
