FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY orchestrator.py \
      schema_specialist.py \
      code_generator.py \
      sandbox.py \
      providers.py \
      usage_tracker.py \
      api_server.py \
      monitor.py \
      ./

# Create directories for auto-generated files
RUN mkdir -p schema code_cache

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPYCACHEPREFIX=/tmp/__pycache__ \
    PYTHONDONTWRITEBYTECODE=1

# Expose port 8100 for API server
EXPOSE 8100

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

# Start FastAPI server
CMD ["python", "api_server.py"]
