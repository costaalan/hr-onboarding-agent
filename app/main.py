"""FastAPI Application - HR Onboarding Agent

Endpoints:
- POST /ask - Envia pergunta e recebe resposta do agente
- GET /health - Health check
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import HROnboardingAgent

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


@app.post("/ask", response_model=AnswerResponse)
def ask(req: QuestionRequest):
    if not req.question.strip():
        return AnswerResponse(
            question=req.question,
            answer="Por favor, digite uma pergunta valida.",
            source="",
        )
    result = agent.ask(req.question)
    return AnswerResponse(**result)


# Servir frontend estatico
STATIC_DIR = Path(__file__).parent.parent / "frontend"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8700, reload=True)
