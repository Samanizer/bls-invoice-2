## backend/Dockerfile
## Builds the FastAPI backend image.
## The /data volume must be mounted at runtime to persist the SQLite database and logo.

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Data directory will be a mounted volume
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
