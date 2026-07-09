"""FastAPI Application - HR Onboarding Agent

Endpoints:
- POST /ask - Envia pergunta e recebe resposta do agente
- GET /health - Health check
"""

import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.agent import HROnboardingAgent
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from fastapi.responses import Response

# --- Rate Limiting Simples por IP ---
RATE_LIMIT_WINDOW = 60        # janela de 60 segundos
RATE_LIMIT_MAX_REQUESTS = 30  # maximo de 30 requisicoes por janela por IP
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> bool:
    """Retorna True se o IP ainda esta dentro do limite, False se excedeu."""
    now = time.time()
    # Remove timestamps fora da janela
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    _rate_limit_store[ip].append(now)
    return True

# Prometheus metrics
HR_QUESTIONS = Counter("hr_questions_total", "Total questions asked", ["status"])
HR_LATENCY = Histogram("hr_latency_seconds", "Question latency", buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0])

app = FastAPI(title="HR Onboarding Agent", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia o agente (singleton)
agent = HROnboardingAgent()


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    source: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "hr-onboarding-agent"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain; charset=utf-8")


@app.post("/ask", response_model=AnswerResponse)
def ask(req: QuestionRequest, request: Request):
    # Rate limiting por IP
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Muitas requisicoes. Tente novamente em alguns segundos."},
        )

    if not req.question.strip():
        return AnswerResponse(
            question=req.question,
            answer="Por favor, digite uma pergunta valida.",
            source="",
        )
    import time
    t0 = time.time()
    try:
        result = agent.ask(req.question)
        HR_QUESTIONS.labels(status="success").inc()
        HR_LATENCY.observe(time.time() - t0)
        return AnswerResponse(**result)
    except Exception:
        HR_QUESTIONS.labels(status="error").inc()
        raise


# Servir frontend estatico
STATIC_DIR = Path(__file__).parent.parent / "frontend"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8700, reload=True)
