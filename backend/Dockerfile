# Production-ready container for Cloud Run
# Notes:
# - Use slim base to reduce cold start and egress costs
# - Avoid GPU dependencies; CPU inference for POC

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    git \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better caching (build context should be backend/)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Application code
COPY . /app

# Ensure pothole model weights are copied into the image at a deterministic path
# If you manage weights via CI/CD download, you may comment this line out.
COPY models/pothole_yolov8n.pt /app/models/pothole_yolov8n.pt

# Non-root user
RUN useradd -m appuser
USER appuser

# Expose port for Cloud Run
ENV PORT=8080
EXPOSE 8080

# Health environment
ENV ENV=production LOG_LEVEL=INFO

# Entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
