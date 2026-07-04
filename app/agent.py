"""Agente LangGraph para HR Onboarding

Grafo com 4 nós:
1. classifier_node - classifica se a pergunta é sobre RH ou fora do escopo
2. retriever_node - busca trechos relevantes no ChromaDB
3. answer_node - gera resposta citando documento fonte
4. fallback_node - responde educadamente quando fora do escopo

Usa OpenRouter com DeepSeek V3 como LLM.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Literal, TypedDict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Caminhos
BASE_DIR = Path(__file__).parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

# Modelo de embeddings (mesmo usado na indexação)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# DeepSeek config
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# Top-K chunks para recuperar
TOP_K = 5


class AgentState(TypedDict):
    question: str
    classification: Optional[str]
    context: Optional[list[dict]]
    answer: Optional[str]
    source: Optional[str]


# LLM via Hermes local
HERMES_URL = os.environ.get("HERMES_URL", "http://localhost:9092")  # porta do Hermes local
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "deepseek-chat")  # modelo configurado no Hermes
# LLM via Hermes config (usa mesma chave do Hermes)
HERMES_BASE_URL = os.environ.get("HERMES_BASE_URL", "https://api.deepseek.com/v1")
HERMES_MODEL = os.environ.get("HERMES_MODEL", "deepseek-chat")
HERMES_API_KEY = os.environ.get("HERMES_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
if not HERMES_API_KEY:
    # Tentar ler do .env
    try:
        for path in ["/opt/data/.env", ".env"]:
            with open(path) as f:
                for line in f:
                    if "DEEPSEEK_API_KEY" in line and "=" in line and not line.strip().startswith("#"):
                        HERMES_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if HERMES_API_KEY: break
    except:
        pass


def call_llm(system: str, prompt: str, max_tokens: int = 300, temperature: float = 0.0) -> str:
    """Chama Ollama Cloud (minimax-m3) via API. Fallback para resposta padrao."""
    ollama_key = os.environ.get("OLLAMA_API_KEY", "")
    if not ollama_key:
        ollama_key = "a4dab60233da462b8cb1096a33c64117.u18mgxcqGWb7YOPUi647zXvP"
    
    headers = {
        "Authorization": f"Bearer {ollama_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "minimax-m3:cloud",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"num_predict": max_tokens},
    }

    req = urllib.request.Request(
        "https://api.ollama.cloud/v1/chat/completions",
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return ""


class HROnboardingAgent:
    """Agente LangGraph para onboarding de RH."""

    def __init__(self):
        print("[AGENT] Inicializando HR Onboarding Agent...")

        # Embeddings
        print("[AGENT] Carregando modelo de embeddings...")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # ChromaDB
        print(f"[AGENT] Conectando ao ChromaDB em: {CHROMA_DIR}")
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_collection("hr_documents")

        # Montar grafo
        self.graph = self._build_graph()
        print("[AGENT] Agente pronto!")

    def _build_graph(self):
        """Constroi o grafo LangGraph."""
        workflow = StateGraph(AgentState)

        workflow.add_node("classifier", self.classifier_node)
        workflow.add_node("retriever", self.retriever_node)
        workflow.add_node("answer", self.answer_node)
        workflow.add_node("fallback", self.fallback_node)
        workflow.add_node("greeting", self.greeting_node)

        workflow.set_entry_point("classifier")

        workflow.add_conditional_edges(
            "classifier",
            self._route_after_classification,
            {"rh": "retriever", "out_of_scope": "fallback", "greeting": "greeting"},
        )

        workflow.add_edge("retriever", "answer")
        workflow.add_edge("answer", END)
        workflow.add_edge("fallback", END)
        workflow.add_edge("greeting", END)

        return workflow.compile()

    def _route_after_classification(self, state: AgentState) -> Literal["rh", "out_of_scope", "greeting"]:
        return state.get("classification", "out_of_scope")

    def classifier_node(self, state: AgentState):
        """Classifica se a pergunta é sobre RH ou fora do escopo."""
        question = state["question"]
        question_lower = question.lower().strip()
        
        # Saudacoes e cumprimentos - rota direta para greeting
        saudacoes = ["oi", "ola", "olá", "bom dia", "boa tarde", "boa noite", "hey", "hello", "hi"]
        if question_lower in saudacoes or any(question_lower.startswith(s) for s in ["oi", "ola", "olá", "bom dia", "boa tarde"]):
            print(f"[CLASSIFIER] Saudacao detectada: '{question[:40]}' -> greeting")
            return {"classification": "greeting"}
        
        # Palavras-chave de RH - deteccao sem depender do LLM
        rh_keywords = [
            "ferias", "ferias", "beneficio", "beneficio", "plano de saude", "plano de saúde",
            "vale alimentacao", "vale alimentação", "vale transporte", "codigo de conduta", "código de conduta",
            "home office", "onboarding", "salario", "salário", "folha de pagamento", "dress code",
            "horario", "horário", "treinamento", "treinamento", "periodo de experiencia", "período de experiência",
            "equipamento", "ponto", "ponto eletronico", "jornada", "carga horaria", "carga horária",
            "seguro", "previdencia", "previdência", "contrato", "admissao", "admissão",
            "rescisao", "rescisão", "holerite", "decimo", "décimo", "13o", "13º",
            "auxilio", "auxílio", "reembolso", "nota fiscal", "vt", "vr", "va",
        ]
        if any(kw in question_lower for kw in rh_keywords):
            print(f"[CLASSIFIER] Palavra-chave RH detectada: '{question[:60]}' -> rh")
            return {"classification": "rh"}
        
        system = "Você classifica perguntas como 'rh' ou 'out_of_scope'. Responda apenas uma palavra."
        prompt = f"""Analise a pergunta abaixo e classifique como "rh" ou "out_of_scope".

Perguntas relacionadas a RH incluem: beneficios, ferias, codigo de conduta, 
home office, onboarding, salario, folha de pagamento, plano de saude, 
vale alimentacao, vale transporte, horario de trabalho, dress code, 
equipamentos, treinamento, periodo de experiencia, e outras questoes 
tipicas de RH empresarial.

Responda APENAS com uma palavra: "rh" ou "out_of_scope".

Pergunta: {question}"""

        classification = call_llm(system, prompt, max_tokens=10, temperature=0).lower()

        if "rh" in classification or "recursos humanos" in classification:
            classification = "rh"
        else:
            classification = "out_of_scope"

        print(f"[CLASSIFIER] Pergunta: '{question[:60]}...' -> {classification}")
        return {"classification": classification}

    def retriever_node(self, state: AgentState):
        """Busca chunks relevantes no ChromaDB."""
        question = state["question"]

        query_embedding = self.embedder.encode(question).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
        )

        contexts = []
        seen_sources = set()

        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                source = results["metadatas"][0][i].get("source", "desconhecido")
                contexts.append({
                    "text": doc,
                    "source": source,
                    "relevance": results["distances"][0][i] if results["distances"] else 0,
                })
                seen_sources.add(source)

        print(f"[RETRIEVER] Encontrados {len(contexts)} chunks de {len(seen_sources)} documentos")
        for ctx in contexts:
            print(f"  -> {ctx['source']} (dist: {ctx['relevance']:.4f})")

        return {"context": contexts}

    def answer_node(self, state: AgentState):
        """Gera resposta citando o documento fonte."""
        question = state["question"]
        contexts = state.get("context", [])

        if not contexts:
            return {
                "answer": "Nao encontrei informacao relevante nos documentos disponiveis. Por favor, contate o RH para mais detalhes.",
                "source": "nenhum",
            }

        context_text = ""
        sources_set = set()
        for i, ctx in enumerate(contexts, 1):
            context_text += f"\n[DOCUMENTO {i}: {ctx['source']}]\n{ctx['text']}\n"
            sources_set.add(ctx['source'])

        sources = ", ".join(sorted(sources_set))

        system = "Você é um assistente de RH amigável e prestativo. Responda de forma natural e conversacional, como um profissional de RH."
        prompt = f'''Você é um assistente de onboarding de RH.

REGRAS:
1. Se for um cumprimento (ola, oi, bom dia), seja caloroso e pergunte como pode ajudar.
2. Para perguntas especificas sobre beneficios, ferias, home office, etc., responda com as informacoes dos documentos.
3. NUNCA mencione nomes de arquivos PDF, documentos ou fontes tecnicas.
4. Responda como se voce fosse uma pessoa do RH conversando naturalmente.
5. Se nao souber a resposta, diga que vai verificar e retorna.

Documentos de referencia (uso interno):
{context_text}

Pergunta do usuario: {question}'''

        answer = call_llm(system, prompt, max_tokens=600, temperature=0.3)
        if not answer:
            # Fallback: responder com informacoes basicas baseadas nos chunks
            fallback_info = ""
            for ctx in contexts[:3]:
                text = ctx['text'][:200]
                fallback_info += text + "\n"
            answer = f"Com base nas informações disponíveis:\n\n{fallback_info[:500]}\n\nSe precisar de mais detalhes, é só perguntar!"
            answer = answer.strip()

        print(f"[ANSWER] Resposta gerada ({len(answer)} chars) - Fontes: {sources}")
        return {"answer": answer, "source": sources}

    def fallback_node(self, state: AgentState):
        """Responde educadamente quando a pergunta está fora do escopo."""
        question = state["question"]

        system = "Você é um assistente de RH. Seja educado ao redirecionar perguntas fora do escopo."
        prompt = f"""Um usuario fez uma pergunta que nao e relacionada a RH.
Responda educadamente que voce é um assistente de onboarding de RH e nao pode 
responder essa pergunta. Sugira que ele pergunte sobre beneficios, ferias, 
codigo de conduta, home office ou onboarding.

Pergunta do usuario: {question}"""

        answer = call_llm(system, prompt, max_tokens=200, temperature=0.3)
        if not answer:
            answer = "Desculpe, sou um assistente especializado em RH e onboarding. Nao posso responder essa pergunta. Pergunte sobre beneficios, ferias, codigo de conduta, home office ou onboarding."

        print("[FALLBACK] Resposta generica gerada")
        return {"answer": answer, "source": "fora_do_escopo"}

    def greeting_node(self, state: AgentState):
        """Responde com boas-vindas naturais, sem jogar tudo de uma vez."""
        answer = """Olá! 😊 Seja muito bem-vindo(a)! Fico feliz em ter você aqui.

Sou o assistente de onboarding da empresa. Estou aqui para ajudar com qualquer dúvida sobre seus primeiros dias, benefícios, férias, horários e tudo mais que precisar.

Pode perguntar à vontade — estou aqui para ajudar! 🚀"""
        return {"answer": answer.strip(), "source": ""}

    def ask(self, question: str) -> dict:
        """Executa o grafo completo e retorna a resposta."""
        initial_state: AgentState = {
            "question": question,
            "classification": None,
            "context": None,
            "answer": None,
            "source": None,
        }

        final_state = self.graph.invoke(initial_state)

        return {
            "question": question,
            "answer": final_state.get("answer", ""),
            "source": final_state.get("source", ""),
        }
