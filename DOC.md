# Desafio 1 - Ingestão e Busca Semântica

Este documento consolida o processo de desenvolvimento do desafio de Ingestão e Busca Semântica, abrangendo a implementação inicial, as correções aplicadas após testes em tempo de execução, a atualização do repositório GitHub e uma explicação objetiva sobre os principais imports utilizados no código, com referência à documentação oficial.

---

## Visão Geral do Desenvolvimento

O projeto foi desenvolvido de forma incremental, iniciando pela ingestão de documentos PDF, passando pela definição do prompt restritivo para busca semântica e culminando na implementação do chat interativo via linha de comando. Durante esse processo, ajustes foram realizados para garantir conformidade total com os requisitos do desafio.

---

## Diagrama de Blocos da Solução

### (1) INGESTÃO

```text
+-------------------------+         +---------------------+         +----------------------+
| PDF(s)                  |         | Splitter            |         | Embeddings           |
| (arquivo local)         +-------->+ chunk=1000          +-------->+ OpenAI ou Gemini     |
|                         |         | overlap=150         |         | (vetores)            |
+-------------------------+         +---------------------+         +----------+-----------+
                                                                               |
                                                                               v
                                                                  +----------------------+
                                                                  | PostgreSQL + pgvector|
                                                                  | (coleção vetorial)   |
                                                                  +-----------+----------+
                                                                              ^
```

### (2) BUSCA SEMÂNTICA + RESPOSTA

```text
+-------------------------+         +---------------------+         +---------+----------+
| Pergunta do usuário     |         | Similarity Search   |         | Contexto Top-K     |
| (CLI)                   +-------->+ PGVector (k=5)      +-------->+ chunks recuperados |
+-------------------------+         +---------------------+         +---------+----------+
                                                                              |
                                                                              v
                                                                  +----------------------+
                                                                  | search.py            |
                                                                  | Monta prompt         |
                                                                  | (regras do desafio)  |
                                                                  +----------+-----------+
                                                                             |
                                                                             v
                                                                  +----------------------+
                                                                  | LLM (Chat)           |
                                                                  | OpenAI ou Gemini     |
                                                                  | temp=0               |
                                                                  +----------+-----------+
                                                                             |
                                                                             v
                                                                  +----------------------+
                                                                  | Resposta ao usuário  |
                                                                  | (somente do contexto)|
                                                                  +----------------------+
```

---

## Interpretação do diagrama

A solução tem dois fluxos independentes:

- **Ingestão**: PDF → chunks → embeddings → armazenamento no pgvector.
- **Consulta**: pergunta → busca vetorial → contexto → prompt → LLM → resposta.

O LLM não recebe o PDF inteiro. Somente os chunks recuperados pela busca vetorial.

O `search.py` impõe as regras que impedem respostas fora do contexto.

---

## Lógica dos Arquivos Python

### ingest.py

**Responsabilidade:** transformar PDFs em vetores armazenados no banco.

**Lógica interna:**

- Carrega variáveis do `.env` (ex.: `PDF_PATH`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`).
- Seleciona o provedor de embeddings (OpenAI ou Gemini) com base nas chaves de `.env`.
- Lê o PDF com `PyPDFLoader`, gerando documentos.
- Divide o conteúdo em chunks usando `RecursiveCharacterTextSplitter` com:
  - `chunk_size = 1000`
  - `chunk_overlap = 150`
- Conecta ao PostgreSQL/pgvector via `PGVector`.
- Insere os chunks no banco com seus embeddings e metadados (ex.: `source`, `page`).

**Ponto de conformidade com o desafio:**

- Chunking e overlap fixos.
- Persistência em pgvector.
- Preparado para OpenAI ou Gemini, conforme permitido.

---

### search.py

**Responsabilidade:** produzir um prompt com regras rígidas para o LLM.

**Lógica interna:**

- Recebe obrigatoriamente:
  - `question`: pergunta do usuário
  - `context`: texto recuperado do banco (string ou lista)
- Normaliza pergunta e contexto para garantir previsibilidade.
- Monta o prompt no formato exigido:
  - Seção “CONTEXTO”
  - Seção “REGRAS” (responder só com base no contexto, negar se insuficiente)
  - Pergunta do usuário
- Retorna a string final do prompt pronta para envio ao LLM.

**Ponto de conformidade com o desafio:**

- Garante que o LLM opere sob regras explícitas.
- Centraliza a política de “não alucinar” em um único lugar.

---

### chat.py

**Responsabilidade:** orquestrar a consulta ponta a ponta.

**Lógica interna:**

- Carrega `.env`.
- Inicializa:
  - embeddings (OpenAI ou Gemini)
  - LLM de chat (OpenAI ou Gemini) com `temperature=0` para reduzir variação
- Conecta ao `PGVector` (mesma collection usada na ingestão).
- Entra em loop no terminal:
  - Lê pergunta do usuário
  - Faz `similarity_search(question, k=5)`
  - Formata documentos recuperados em um bloco de contexto (com limite de tamanho)
  - Gera o prompt chamando `search_prompt(question, context)`
  - Envia para o LLM (`llm.invoke(prompt)`)
  - Exibe a resposta
  - Permite sair com `exit/quit/sair`.

**Ponto de conformidade com o desafio:**

- O LLM recebe apenas o contexto recuperado.
- Mantém execução via CLI.
- Sem memória externa.

---

## Observação de engenharia

A separação em três arquivos reduz acoplamento e aumenta clareza:

- `ingest.py`: etapa offline/assíncrona (pode rodar uma vez por documento).
- `chat.py`: etapa online/síncrona (tempo de resposta do usuário).
- `search.py`: política de resposta (governança), aplicada sempre.

Isso torna a solução:

- mais testável (cada módulo pode ser validado isoladamente),
- mais fácil de evoluir (ex.: trocar embeddings, mudar k, re-ranking),
- mais consistente com práticas reais de desenvolvimento de aplicações de IA.

---

## Desenvolvimento Inicial e Evolução do Fluxo

Na etapa inicial, os módulos `ingest.py`, `search.py` e `chat.py` foram estruturados para atender à arquitetura proposta. A evolução do fluxo ocorreu a partir da identificação de erros de uso indevido das funções, resultando na consolidação de um fluxo definitivo.

---

## Correções Aplicadas Após Execução

Durante a execução do chat semântico, foi identificado um erro relacionado à ausência da pergunta do usuário no momento da geração do prompt. A correção garantiu que a pergunta e o contexto recuperado do banco vetorial fossem sempre fornecidos.

---

## Conformidade com o Desafio

Após as correções, o projeto passou a cumprir integralmente os requisitos do desafio, incluindo uso exclusivo do contexto recuperado, ausência de memória externa e operação via CLI.

---

## Explicação dos Imports Utilizados

A seguir, apresenta-se uma explicação resumida dos principais imports utilizados no projeto, bem como os links para a documentação oficial de cada biblioteca ou módulo.

### dotenv (python-dotenv)

O módulo `dotenv` é utilizado para carregar variáveis de ambiente a partir do arquivo `.env`, permitindo separar configuração de código-fonte.

Documentação oficial: https://pypi.org/project/python-dotenv/

### PyPDFLoader (LangChain Community)

Responsável por realizar a leitura e extração de texto de arquivos PDF, convertendo-os em documentos compatíveis com o ecossistema LangChain.

Documentação oficial: https://python.langchain.com/docs/integrations/document_loaders/pypdfloader/

### RecursiveCharacterTextSplitter (LangChain)

Utilizado para dividir textos extensos em fragmentos menores (chunks), respeitando tamanho máximo e sobreposição, conforme exigido no desafio.

Documentação oficial: https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter/

### PGVector (langchain-postgres)

Classe responsável pela integração entre LangChain e PostgreSQL com extensão pgvector, permitindo persistir e consultar embeddings vetoriais.

Documentação oficial: https://python.langchain.com/docs/integrations/vectorstores/pgvector/

### OpenAIEmbeddings e ChatOpenAI

Classes utilizadas para geração de embeddings e interação com modelos de linguagem da OpenAI.

Documentação oficial: https://python.langchain.com/docs/integrations/text_embedding/openai/

Documentação oficial (Chat): https://python.langchain.com/docs/integrations/chat/openai/

### GoogleGenerativeAIEmbeddings e ChatGoogleGenerativeAI

Classes utilizadas para geração de embeddings e interação com modelos Gemini.

Documentação oficial: https://python.langchain.com/docs/integrations/text_embedding/google_generative_ai/

Documentação oficial (Chat): https://python.langchain.com/docs/integrations/chat/google_generative_ai/

---

## Execução do Projeto

```bash
docker compose up -d
python src/ingest.py
python src/chat.py
```

---

## Atualização do Repositório GitHub

Após a implementação e correções, o repositório GitHub deve ser atualizado para refletir o estado final do projeto.

```bash
git add .
git commit -m "Implementação inicial do desafio de ingestão e busca"
git push origin main
```

---

## Considerações Finais

A realização deste desafio consolidou, de forma prática, conceitos centrais para o desenvolvimento de aplicações apoiadas por Inteligência Artificial, especialmente no contexto de IA aplicada a dados próprios. Ao longo do trabalho, foi possível integrar ingestão de documentos, geração de embeddings, persistência vetorial e busca semântica controlada, respeitando rigorosamente o princípio de que o modelo de linguagem deve responder exclusivamente com base no contexto fornecido. Esse ponto é fundamental para aplicações reais, nas quais confiabilidade, rastreabilidade da informação e controle de alucinações são requisitos técnicos e não apenas boas práticas teóricas.

Do ponto de vista de engenharia de software, o desafio reforça a importância de uma arquitetura bem definida, com separação clara de responsabilidades entre ingestão, recuperação, construção de prompt e interação com o modelo de linguagem. A utilização de PostgreSQL com pgvector demonstra como tecnologias tradicionais de banco de dados podem ser estendidas para suportar casos modernos de IA permitindo soluções escaláveis, auditáveis e alinhadas a ambientes corporativos. Além disso, o uso de ferramentas como LangChain evidencia a relevância de frameworks que abstraem a complexidade de integração com LLMs sem perder controle sobre o fluxo de dados.

Em termos de relevância para o desenvolvimento de aplicações apoiadas por IA, este desafio exemplifica um padrão arquitetural cada vez mais adotado no mercado: RAG (Retrieval-Augmented Generation). Esse padrão permite combinar o poder generativo dos modelos de linguagem com dados específicos do domínio, reduzindo riscos, aumentando a precisão das respostas e viabilizando aplicações como assistentes corporativos, sistemas de suporte à decisão, análise documental e busca inteligente em grandes volumes de informação.

O projeto pode evoluir em diversas direções. Entre elas, destacam-se a implementação de métricas de qualidade da busca (como avaliação de similaridade e relevância), a inclusão de testes automatizados para validar respostas negativas e positivas, o tratamento de múltiplos documentos e coleções, e a incorporação de camadas de segurança e controle de acesso. Em um cenário mais avançado, também seria possível explorar técnicas de re-ranking, caching de respostas e observabilidade do uso do sistema, aproximando ainda mais a solução de um ambiente de produção.

Em síntese, o desafio não apenas cumpre seus objetivos técnicos, mas também serve como uma base sólida para compreender e aplicar, de forma responsável e profissional, os principais padrões atuais no desenvolvimento de soluções de IA generativa orientadas a dados reais.
