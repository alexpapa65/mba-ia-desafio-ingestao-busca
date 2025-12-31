import os
import sys

from dotenv import load_dotenv

from langchain_postgres import PGVector

from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from search import search_prompt

load_dotenv()


def _get_env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name, default)
    if v is None:
        return None
    return v.strip().strip("'").strip('"')


def _get_embeddings():
    openai_key = _get_env("OPENAI_API_KEY")
    google_key = _get_env("GOOGLE_API_KEY")

    if openai_key:
        model = _get_env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        return "openai", OpenAIEmbeddings(model=model)

    if google_key:
        model = _get_env("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
        return "google", GoogleGenerativeAIEmbeddings(model=model)

    raise RuntimeError("Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env para embeddings.")


def _get_llm():
    # Prioridade igual à de embeddings: OpenAI se houver chave, senão Google
    openai_key = _get_env("OPENAI_API_KEY")
    google_key = _get_env("GOOGLE_API_KEY")

    if openai_key:
        model = _get_env("OPENAI_LLM_MODEL", "gpt-4o-mini")
        return "openai", ChatOpenAI(model=model, temperature=0)

    if google_key:
        model = _get_env("GOOGLE_LLM_MODEL", "gemini-2.5-flash-lite")
        return "google", ChatGoogleGenerativeAI(model=model, temperature=0)

    raise RuntimeError("Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env para LLM.")


def _get_vectorstore(embeddings):
    db_url = _get_env("DATABASE_URL")
    collection = _get_env("PG_VECTOR_COLLECTION_NAME")

    if not db_url:
        raise RuntimeError("DATABASE_URL não definido no .env")
    if not collection:
        raise RuntimeError("PG_VECTOR_COLLECTION_NAME não definido no .env")

    return PGVector(
        connection=db_url,
        collection_name=collection,
        embeddings=embeddings,
        use_jsonb=True,
    )


def _format_context(docs, max_chars: int = 6000) -> str:
    """
    Concatena os chunks recuperados em um bloco de contexto.
    Limita o tamanho para evitar prompts enormes.
    """
    if not docs:
        return ""

    parts = []
    total = 0
    for d in docs:
        text = getattr(d, "page_content", "") or ""
        text = text.strip()
        if not text:
            continue

        # separador entre trechos
        candidate = text + "\n\n"
        if total + len(candidate) > max_chars:
            break
        parts.append(text)
        total += len(candidate)

    return "\n\n".join(parts).strip()


def main():
    provider_e, embeddings = _get_embeddings()
    provider_l, llm = _get_llm()

    vectorstore = _get_vectorstore(embeddings)

    print("Chat semântico iniciado.")
    print(f"Embeddings: {provider_e}")
    print(f"LLM: {provider_l}")
    print("Digite sua pergunta e pressione Enter. Para sair, digite: exit\n")

    while True:
        try:
            question = input("Pergunta> ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit", "sair"):
                break

            # Busca semântica (top-k)
            # k pode ser ajustado, mas 4-6 costuma ser suficiente
            docs = vectorstore.similarity_search(question, k=5)

            context_text = _format_context(docs)

            # Monta prompt restritivo
            prompt = search_prompt(question=question, context=context_text)

            # Envia para o LLM
            response = llm.invoke(prompt)

            # Em LangChain, Chat models retornam AIMessage com content
            answer = getattr(response, "content", str(response)).strip()

            print("\nResposta:")
            print(answer)
            print()

        except KeyboardInterrupt:
            print("\nEncerrando.")
            break
        except Exception as e:
            print(f"\nErro: {e}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
