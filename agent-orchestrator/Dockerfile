FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY orchestrator.py .

# Environment variables can be provided by docker-compose (.env file) at runtime.
# Expose the API port (adjust in docker-compose as needed)
EXPOSE 8000

# Run orchestrator API (FastAPI app will be added/used in orchestrator.py)
CMD ["python", "orchestrator.py"]
