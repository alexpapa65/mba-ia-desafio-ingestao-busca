import os
import sys
import argparse
from typing import Optional

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_postgres import PGVector

from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings


# Carrega variáveis do .env
load_dotenv()


# Requisitos fixos
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip().strip("'").strip('"')
    return value


def get_embeddings():
    """
    Seleciona o provedor de embeddings com base nas variáveis de ambiente.
    Prioridade:
    - OpenAI se OPENAI_API_KEY estiver definido
    - Google Gemini se GOOGLE_API_KEY estiver definido
    """
    openai_key = _get_env("OPENAI_API_KEY")
    google_key = _get_env("GOOGLE_API_KEY")

    if openai_key:
        model = _get_env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        return "openai", OpenAIEmbeddings(model=model)

    if google_key:
        model = _get_env("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
        return "google", GoogleGenerativeAIEmbeddings(model=model)

    raise RuntimeError(
        "Nenhuma API Key encontrada. Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env."
    )


def validate_env(pdf_path: str, db_url: str, collection: str):
    if not pdf_path or not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    if not db_url:
        raise ValueError("DATABASE_URL não definido no .env")

    if not collection:
        raise ValueError("PG_VECTOR_COLLECTION_NAME não definido no .env")


def ingest_pdf(pdf_path: str, db_url: str, collection: str):
    provider, embeddings = get_embeddings()

    # 1. Carregar PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    if not documents:
        raise RuntimeError("Nenhum conteúdo foi extraído do PDF.")

    # 2. Split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise RuntimeError("Nenhum chunk gerado a partir do PDF.")

    # 3. Banco vetorial (pgvector)
    vectorstore = PGVector(
        connection=db_url,
        collection_name=collection,
        embeddings=embeddings,
        use_jsonb=True,
    )

    # Garantir metadados mínimos exigidos
    for doc in chunks:
        doc.metadata = doc.metadata or {}
        doc.metadata.setdefault("source", pdf_path)

    vectorstore.add_documents(chunks)

    # Logs finais (úteis para avaliação)
    print("Ingestão finalizada com sucesso")
    print(f"Provedor de embeddings: {provider}")
    print(f"PDF ingerido: {pdf_path}")
    print(f"Páginas carregadas: {len(documents)}")
    print(f"Chunks gerados: {len(chunks)}")
    print(f"Collection pgvector: {collection}")


def parse_args():
    parser = argparse.ArgumentParser(description="Ingestão de PDFs para busca semântica")
    parser.add_argument(
        "--pdf",
        default=_get_env("PDF_PATH"),
        help="Caminho do PDF a ser ingerido (ou PDF_PATH no .env)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()

        pdf_path = args.pdf
        db_url = _get_env("DATABASE_URL")
        collection = _get_env("PG_VECTOR_COLLECTION_NAME")

        validate_env(pdf_path, db_url, collection)
        ingest_pdf(pdf_path, db_url, collection)

    except Exception as error:
        print(f"Erro durante a ingestão: {error}", file=sys.stderr)
        sys.exit(1)
