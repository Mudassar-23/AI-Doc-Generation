FROM python:3.11-slim

WORKDIR /app

# Install git (needed for cloning repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy shared code
COPY backend/ /app/backend/
COPY runner/ /app/runner/
COPY templates/ /app/templates/

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Create directories
RUN mkdir -p /app/outputs /app/tmp /app/data

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
