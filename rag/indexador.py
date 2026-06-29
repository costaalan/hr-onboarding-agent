"""Pipeline de Indexação RAG para o HR Onboarding Agent

Extrai texto dos PDFs, gera embeddings com sentence-transformers
e indexa no ChromaDB.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader


DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
PDF_DIR = DATA_DIR

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extract text from PDF, returning chunks with source metadata."""
    reader = PdfReader(str(pdf_path))
    chunks = []
    filename = Path(pdf_path).name

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if not text or not text.strip():
            continue

        # Split by newlines, then group into meaningful chunks
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        current_chunk = ""

        for line in lines:
            # If line looks like a section header or is long enough, start new chunk
            is_header = line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))
            if is_header and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "source": filename,
                    "page": page_num,
                })
                current_chunk = line + " "
            elif len(current_chunk) + len(line) > 600:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "source": filename,
                        "page": page_num,
                    })
                current_chunk = line + " "
            else:
                current_chunk += line + " "

        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "source": filename,
                "page": page_num,
            })

    return chunks


def index_documents():
    """Extract, embed, and index all PDF documents into ChromaDB."""
    print("[RAG] Inicializando modelo de embeddings...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"[RAG] Inicializando ChromaDB em: {CHROMA_DIR}")
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        client.delete_collection("hr_documents")
        print("[RAG] Colecao antiga removida")
    except Exception:
        pass

    collection = client.create_collection(
        name="hr_documents",
        metadata={"hnsw:space": "cosine"},
    )

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"[RAG] Encontrados {len(pdf_files)} PDFs para indexar")

    all_chunks = []
    for pdf_path in pdf_files:
        print(f"  -> Extraindo: {pdf_path.name}")
        chunks = extract_text_from_pdf(str(pdf_path))
        all_chunks.extend(chunks)
        print(f"     {len(chunks)} chunks extraidos")

    print(f"\n[RAG] Total de {len(all_chunks)} chunks para indexar")

    texts = [c["text"] for c in all_chunks]
    metadatas = [{"source": c["source"], "page": c["page"]} for c in all_chunks]
    ids = [f"doc_{i}" for i in range(len(all_chunks))]

    # Generate embeddings and add to collection
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_metas = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]

        print(f"  -> Gerando embeddings lote {i//batch_size + 1} ({len(batch_texts)} chunks)...")
        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        collection.add(
            documents=batch_texts,
            embeddings=embeddings,
            metadatas=batch_metas,
            ids=batch_ids,
        )

    print(f"\n[RAG] Indexacao concluida!")
    print(f"  - Total de chunks: {len(all_chunks)}")
    print(f"  - Documentos: {len(pdf_files)}")
    print(f"  - Colecao: hr_documents")
    print(f"  - Storage: {CHROMA_DIR}")
    return collection, model


if __name__ == "__main__":
    index_documents()
