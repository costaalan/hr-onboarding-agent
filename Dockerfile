FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Index documents into ChromaDB
RUN python rag/indexador.py

EXPOSE 8700

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8700"]
