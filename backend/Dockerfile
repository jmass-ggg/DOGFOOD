# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application code and dependency definition
COPY pyproject.toml ./
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./

RUN pip install --no-cache-dir . && useradd --system --uid 10001 dogfood
USER dogfood

# Expose port 8000 for FastAPI
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run uvicorn as entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
