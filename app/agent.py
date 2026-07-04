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


def call_llm(system: str, prompt: str, max_tokens: int = 300, temperature: float = 0.0) -> str:
    """Chama DeepSeek API via HTTP."""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    req = urllib.request.Request(
        DEEPSEEK_URL,
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

        system = "Você é um assistente de RH que responde com base em documentos da empresa. Sempre cite as fontes."
        prompt = f'''Você é um assistente de RH amigável e prestativo chamado "Assistente de Onboarding RH".

REGRAS IMPORTANTES:
1. Se o usuario estiver dizendo "ola", "oi", "bom dia", ou QUALQUER cumprimento sem uma pergunta especifica, 
   responda IMEDIATAMENTE com boas-vindas calorosas e completas para um novo funcionario.
   Inclua: sistemas (Slack, Google Workspace, PontoTel, PipeDrive, Notion, Jira, Wellhub, Flash),
   horario (8h diarias, 44h semanais, flexivel 7h-19h),
   treinamentos obrigatorios nos primeiros 15 dias,
   auxilio home office (R$ 150/mes),
   e codigo de conduta.

2. Se for uma pergunta especifica sobre RH (beneficios, ferias, plano de saude, etc.),
   use APENAS as informacoes dos documentos abaixo para responder.

3. Se nao encontrar a informacao nos documentos, diga que nao encontrou e sugira contatar o RH.

Documentos de referencia:
{context_text}

Pergunta do usuario: {question}'''

        answer = call_llm(system, prompt, max_tokens=600, temperature=0.3)
        if not answer:
            answer = "Desculpe, nao consegui processar sua pergunta no momento. Tente novamente mais tarde."

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
        """Responde com boas-vindas completas ao novo funcionario."""
        answer = """Olá! Seja muito bem-vindo(a)! 😊 Fico feliz em ter você aqui para iniciar essa jornada conosco.

Com base nos documentos que tenho disponíveis, aqui estão as principais informações para o seu início:

**Sistemas que você vai usar:**
- **Slack** (comunicação interna, canais: #geral, #onboarding, #seutime)
- **Google Workspace** (e-mail, calendário e documentos)
- **PontoTel** (registro de ponto diário)
- **PipeDrive** (CRM, se aplicável ao seu cargo)
- **Notion** (documentação interna e wikis)
- **Jira** (gestão de tarefas, se aplicável ao seu cargo)
- **Wellhub** (benefício de academias)
- **Flash** (cartão de alimentação e refeição)

**Horário de Trabalho:**
A jornada regular é de 8 horas diárias (44 horas semanais), de segunda a sexta-feira, com horário flexível entre 7h e 19h. Você deve cumprir 8 horas líquidas de trabalho com intervalo mínimo de 1 hora de almoço. O registro de ponto é obrigatório (inclusive em home office) e deve ser feito no sistema PontoTel até as 9h e ao final do expediente.

**Treinamentos Obrigatórios (nos primeiros 15 dias):**
Você precisa completar:
1. Treinamento de Segurança da Informação (1h, plataforma EAD)
2. Código de Conduta (leitura e termo de ciência)
3. Apresentação da Cultura e Valores da Empresa (2h presencial ou Zoom)
4. Treinamento dos sistemas que utilizará no dia a dia

Todos os treinamentos são agendados pelo RH e você receberá os links por e-mail.

**Auxílio Home Office:**
Se você estiver em regime de home office, receberá um auxílio mensal de R$ 150,00 para despesas de internet e energia elétrica, pago junto com o salário, sem necessidade de comprovação.

**Código de Conduta:**
Espera-se que todos ajam com integridade, respeito, responsabilidade e transparência. O descumprimento pode resultar em advertências, suspensões ou demissão por justa causa.

Se tiver qualquer dúvida ou precisar de mais informações, fique à vontade para perguntar! Estou aqui para ajudar.

*Fontes: codigo_conduta.pdf, onboarding_geral.pdf, beneficios.pdf, politica_home_office.pdf*
"""
        return {"answer": answer.strip(), "source": "codigo_conduta.pdf, onboarding_geral.pdf, beneficios.pdf, politica_home_office.pdf"}

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
