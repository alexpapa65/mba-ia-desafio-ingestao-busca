PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def _normalize_question(question: str) -> str:
    """
    Normaliza a pergunta para reduzir erros de formatação e garantir previsibilidade
    do prompt. Não altera o sentido do texto.
    """
    if question is None:
        return ""
    q = str(question).strip()
    # Evita perguntas vazias e melhora o formato final do prompt
    return q


def _normalize_context(context) -> str:
    """
    Normaliza o contexto para string.
    Aceita:
      - string
      - lista/tupla de strings
      - lista/tupla de objetos com atributo 'page_content' (ex.: LangChain Document)
    """
    if context is None:
        return ""

    # Se for string, apenas faz strip
    if isinstance(context, str):
        return context.strip()

    # Se for lista/tupla, tenta montar um bloco de contexto
    if isinstance(context, (list, tuple)):
        parts = []
        for item in context:
            if item is None:
                continue
            if isinstance(item, str):
                s = item.strip()
                if s:
                    parts.append(s)
                continue

            # Suporte a objetos estilo LangChain Document (page_content)
            page_content = getattr(item, "page_content", None)
            if isinstance(page_content, str):
                s = page_content.strip()
                if s:
                    parts.append(s)
                continue

            # Fallback: serializa para string
            s = str(item).strip()
            if s:
                parts.append(s)

        return "\n\n".join(parts).strip()

    # Fallback genérico
    return str(context).strip()


def search_prompt(question=None, context=None):
    """
    Gera o prompt final, inserindo PERGUNTA e CONTEXTO.

    Parâmetros:
      - question: string da pergunta do usuário
      - context: contexto recuperado do banco vetorial (string, lista de strings
                ou lista de Document do LangChain)

    Retorna:
      - string do prompt final (PROMPT_TEMPLATE preenchido)

    Observação:
      A lógica de busca semântica (recuperação do contexto) não é responsabilidade
      deste arquivo; aqui só garantimos a construção do prompt com as regras.
    """
    pergunta = _normalize_question(question)
    contexto = _normalize_context(context)

    if not pergunta:
        raise ValueError("Pergunta do usuário não informada (question está vazio).")

    # Se não houver contexto, ainda assim geramos o prompt — o LLM deve responder
    # com a frase padrão conforme as regras.
    return PROMPT_TEMPLATE.format(contexto=contexto, pergunta=pergunta)
