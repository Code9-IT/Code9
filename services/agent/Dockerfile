# =============================================================
# Maritime Agent – FastAPI service
# =============================================================
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# --reload is fine for local dev; remove for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
