# Graph Report - .  (2026-07-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 73 nodes · 90 edges · 20 communities (8 shown, 12 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8286cb46`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_HR Onboarding Agent|HR Onboarding Agent]]
- [[_COMMUNITY_HRPDF|HRPDF]]
- [[_COMMUNITY_main.py|main.py]]
- [[_COMMUNITY_HROnboardingAgent|HROnboardingAgent]]
- [[_COMMUNITY_agent.py|agent.py]]
- [[_COMMUNITY_indexador.py|indexador.py]]
- [[_COMMUNITY_AgentState|AgentState]]
- [[_COMMUNITY_Retriever Node|Retriever Node]]
- [[_COMMUNITY_.classifier_node|.classifier_node]]
- [[_COMMUNITY_.fallback_node|.fallback_node]]
- [[_COMMUNITY_Classifier Node|Classifier Node]]
- [[_COMMUNITY_FastAPI|FastAPI]]
- [[_COMMUNITY_LangGraph|LangGraph]]
- [[_COMMUNITY_Sentence-Transformers|Sentence-Transformers]]
- [[_COMMUNITY_Anthropic|Anthropic]]
- [[_COMMUNITY_Pydantic|Pydantic]]
- [[_COMMUNITY_PyPDF2|PyPDF2]]
- [[_COMMUNITY_Python-Dotenv|Python-Dotenv]]
- [[_COMMUNITY_Python-Multipart|Python-Multipart]]
- [[_COMMUNITY_Uvicorn|Uvicorn]]

## God Nodes (most connected - your core abstractions)
1. `HR Onboarding Agent` - 17 edges
2. `HROnboardingAgent` - 13 edges
3. `AgentState` - 8 edges
4. `HRPDF` - 8 edges
5. `call_llm()` - 5 edges
6. `QuestionRequest` - 4 edges
7. `AnswerResponse` - 4 edges
8. `generate_pdfs()` - 4 edges
9. `Retriever Node` - 4 edges
10. `ask()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `HR Onboarding Service` --references--> `HR Onboarding Agent`  [EXTRACTED]
  docker-compose.yml → README.md
- `Frontend Chat Interface` --references--> `HR Onboarding Agent`  [EXTRACTED]
  frontend/index.html → README.md
- `ChromaDB` --conceptually_related_to--> `ChromaDB`  [INFERRED]
  requirements.txt → README.md
- `FastAPI` --conceptually_related_to--> `FastAPI`  [INFERRED]
  requirements.txt → README.md
- `LangGraph` --conceptually_related_to--> `LangGraph`  [INFERRED]
  requirements.txt → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Agent Pipeline Nodes** — readme_classifier_node, readme_retriever_node, readme_answer_node, readme_fallback_node [EXTRACTED 1.00]
- **RAG Components** — readme_retriever_node, readme_chromadb, readme_answer_node, readme_deepseek_v3, readme_sentence_transformers [EXTRACTED 1.00]

## Communities (20 total, 12 thin omitted)

### Community 0 - "HR Onboarding Agent"
Cohesion: 0.25
Nodes (9): HR Onboarding Service, Frontend Chat Interface, Cloudflare Tunnel, Docker, HR Onboarding Agent, Python 3.12, RAG (Retrieval-Augmented Generation), TailwindCSS (+1 more)

### Community 1 - "HRPDF"
Cohesion: 0.33
Nodes (3): FPDF, generate_pdfs(), HRPDF

### Community 2 - "main.py"
Cohesion: 0.36
Nodes (5): AnswerResponse, ask(), QuestionRequest, FastAPI Application - HR Onboarding Agent  Endpoints: - POST /ask - Envia pergun, BaseModel

### Community 3 - "HROnboardingAgent"
Cohesion: 0.33
Nodes (4): HROnboardingAgent, Constroi o grafo LangGraph., Executa o grafo completo e retorna a resposta., Agente LangGraph para onboarding de RH.

### Community 4 - "agent.py"
Cohesion: 0.33
Nodes (4): call_llm(), Agente LangGraph para HR Onboarding  Grafo com 4 nós: 1. classifier_node - class, Gera resposta citando o documento fonte., Chama DeepSeek API via HTTP.

### Community 5 - "indexador.py"
Cohesion: 0.40
Nodes (5): extract_text_from_pdf(), index_documents(), Pipeline de Indexação RAG para o HR Onboarding Agent  Extrai texto dos PDFs, ger, Extract text from PDF, returning chunks with source metadata., Extract, embed, and index all PDF documents into ChromaDB.

### Community 6 - "AgentState"
Cohesion: 0.40
Nodes (3): AgentState, Busca chunks relevantes no ChromaDB., TypedDict

### Community 7 - "Retriever Node"
Cohesion: 0.40
Nodes (5): Answer Node, ChromaDB, DeepSeek V3, Retriever Node, ChromaDB

## Knowledge Gaps
- **16 isolated node(s):** `RAG (Retrieval-Augmented Generation)`, `Cloudflare Tunnel`, `WSGI Middleware`, `Docker`, `Python 3.12` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HROnboardingAgent` connect `HROnboardingAgent` to `main.py`, `agent.py`, `AgentState`, `.classifier_node`, `.fallback_node`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `HR Onboarding Agent` connect `HR Onboarding Agent` to `Retriever Node`, `Classifier Node`, `FastAPI`, `LangGraph`, `Sentence-Transformers`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `AgentState` connect `AgentState` to `.classifier_node`, `.fallback_node`, `HROnboardingAgent`, `agent.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `HROnboardingAgent` (e.g. with `AnswerResponse` and `QuestionRequest`) actually correct?**
  _`HROnboardingAgent` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Agente LangGraph para HR Onboarding  Grafo com 4 nós: 1. classifier_node - class`, `Chama DeepSeek API via HTTP.`, `Agente LangGraph para onboarding de RH.` to the rest of the system?**
  _29 weakly-connected nodes found - possible documentation gaps or missing edges._