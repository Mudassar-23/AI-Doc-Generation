FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (git for cloning repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
COPY runner/requirements.txt /app/runner/requirements.txt
COPY requirements-dev.txt /app/requirements-dev.txt

# Install all Python dependencies
RUN pip install --no-cache-dir -r /app/requirements-dev.txt

# Copy application code
COPY backend/ /app/backend/
COPY runner/ /app/runner/
COPY templates/ /app/templates/
COPY frontend/ /app/frontend/

# Create required runtime directories
RUN mkdir -p /app/outputs /app/tmp /app/data

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
