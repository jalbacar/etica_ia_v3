FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent.py .

# Ejecutar el agente directamente (no con uvicorn)
CMD ["python", "agent.py"]
