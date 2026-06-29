# HR Onboarding Agent

Assistente inteligente de onboarding para RH que responde perguntas de novos funcionários em linguagem natural sobre benefícios, férias, políticas e plano de saúde — usando **RAG** sobre documentos da empresa.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    Cloudflare Tunnel                 │
│                  alancosta.dev/hr-onboarding         │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           WSGI Middleware (Proxy reverso)            │
│         /hr-onboarding → localhost:8700              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                FastAPI (Porta 8700)                  │
│              app.main: HROnboardingAgent             │
├─────────────────────────────────────────────────────┤
│                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│   │Classifier│───▶│Retriever │───▶│  Answer  │      │
│   │   Node   │    │   Node   │    │   Node   │      │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘      │
│        │               │               │             │
│     out_of_scope       │               │             │
│        │          ChromaDB         DeepSeek V3      │
│   ┌────▼─────┐    (Vector DB)     (via API)         │
│   │ Fallback │                                        │
│   │   Node   │                                        │
│   └──────────┘                                        │
└───────────────────────────────────────────────────────┘
```

O fluxo funciona assim:

1. **Classifier Node** — classifica se a pergunta é sobre RH ou fora do escopo
2. **Retriever Node** — busca os trechos mais relevantes no ChromaDB usando embeddings
3. **Answer Node** — gera resposta em linguagem natural citando os documentos fonte
4. **Fallback Node** — responde educadamente quando a pergunta está fora do escopo

## Stack

| Tecnologia | Finalidade |
|---|---|
| **Python 3.12** | Linguagem base |
| **FastAPI** | API REST |
| **LangGraph** | Orquestração do agente com grafo de nós |
| **ChromaDB** | Vector store local para embeddings |
| **DeepSeek V3** | LLM via API |
| **Sentence-Transformers** | Modelo de embeddings (all-MiniLM-L6-v2) |
| **HTML + TailwindCSS** | Interface web |
| **Docker + docker-compose** | Containerização |

## Como rodar localmente

```bash
# Clone
git clone https://github.com/alncosta1981/hr-onboarding-agent.git
cd hr-onboarding-agent

# Configure a chave DeepSeek
cp .env.example .env
# Edite .env com sua DEEPSEEK_API_KEY

# Opção 1: Docker
docker compose up -d
# Acesse: http://localhost:8700

# Opção 2: Python direto
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python rag/indexador.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8700
```

## API

```json
POST /ask
{
  "question": "Quantos dias de férias eu tenho direito?"
}

{
  "question": "Quantos dias de férias eu tenho direito?",
  "answer": "Você tem direito a 30 dias corridos de férias...",
  "source": "politica_ferias.pdf"
}
```

## Projeto ao vivo

[https://alancosta.dev/hr-onboarding](https://alancosta.dev/hr-onboarding)

## Licença

MIT
