# Ingestão e Busca Semântica com LangChain e PostgreSQL

Este repositório contém a implementação do desafio **Ingestão e Busca Semântica com LangChain e PostgreSQL**, conforme especificado pelo MBA em Inteligência Artificial da Full Cycle.

A solução implementa um sistema de linha de comando (CLI) capaz de ingerir documentos PDF, gerar embeddings, armazená-los em um banco de dados PostgreSQL com extensão pgvector e responder perguntas com base exclusivamente no conteúdo recuperado.

---

## Objetivo

Desenvolver um software capaz de:

- Ingerir documentos PDF
- Dividir o conteúdo em blocos de texto (chunks)
- Gerar embeddings vetoriais
- Persistir os vetores em banco de dados PostgreSQL com pgvector
- Realizar busca semântica
- Responder perguntas utilizando exclusivamente o contexto recuperado do banco de dados

Conforme exigido, o modelo **não deve inventar respostas**. Caso não haja informações suficientes no contexto recuperado, o sistema deve informar explicitamente que não é possível responder à pergunta.

---

## Tecnologias Obrigatórias

As seguintes tecnologias foram utilizadas, conforme exigência do desafio:

- Python
- LangChain
- PostgreSQL
- pgvector
- Docker
- Docker Compose
- OpenAI ou Google Gemini

---

## Estrutura do Projeto

A estrutura do projeto segue exatamente o modelo definido:

```
mba-ia-desafio-ingestao-busca/
│
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── README.md
│
└── src/
    ├── ingest.py
    ├── chat.py
    └── db.py
```

---

## Requisitos de Execução

- Docker e Docker Compose instalados
- Python 3.10 ou superior
- Ambiente virtual Python (venv)
- Chave de acesso válida para OpenAI ou Google Gemini

---

## Configuração do Ambiente

### 1. Clonagem do Repositório

```bash
git clone https://github.com/alexpapa65/mba-ia-desafio-ingestao-busca.git
cd mba-ia-desafio-ingestao-busca
```

---

### 2. Criação e Ativação do Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Instalação das Dependências

```bash
pip install -r requirements.txt
```

---

### 4. Configuração das Variáveis de Ambiente

Crie o arquivo `.env` a partir do exemplo fornecido:

```bash
cp .env.example .env
```

Configure **uma** das opções abaixo.

#### OpenAI

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

Modelos utilizados:
- Embeddings: text-embedding-3-small
- LLM: gpt-4o-mini

#### Google Gemini

```env
GOOGLE_API_KEY=xxxxxxxxxxxxxxxx
```

Modelos utilizados:
- Embeddings: models/embedding-001
- LLM: gemini-2.5-flash-lite

---

## Banco de Dados Vetorial

O banco de dados PostgreSQL com extensão pgvector é executado via Docker Compose.

Para iniciar o banco:

```bash
docker compose up -d
```

---

## Ingestão de Documentos

A ingestão dos documentos PDF é realizada pelo script:

```bash
python src/ingest.py
```

Durante o processo de ingestão:

- O PDF é carregado
- O texto é dividido em blocos de até 1000 caracteres
- É aplicado overlap de 150 caracteres
- São gerados embeddings vetoriais
- Os vetores são armazenados no PostgreSQL com pgvector

---

## Busca Semântica

A busca semântica é realizada por meio do script:

```bash
python src/chat.py
```

Fluxo de execução:

1. O usuário informa uma pergunta via CLI
2. O sistema realiza a busca semântica no banco vetorial
3. Os trechos mais relevantes são recuperados
4. O modelo de linguagem recebe exclusivamente o contexto recuperado
5. A resposta é gerada respeitando integralmente as regras definidas

---

## Estrutura do Prompt

O prompt utilizado segue o formato definido:

```
CONTEXTO:
(conteúdo recuperado do banco de dados)

REGRAS:
- Responder somente com base no CONTEXTO
- Caso não exista informação suficiente, informar que não é possível responder
- Não inventar informações

PERGUNTA DO USUÁRIO:
(pergunta)

RESPOSTA:
```

---

## Ordem de Execução

A ordem correta de execução do projeto é:

```bash
docker compose up -d
python src/ingest.py
python src/chat.py
```

---

## Critérios Atendidos

Este projeto atende integralmente aos critérios definidos:

- Uso das tecnologias obrigatórias
- Ingestão de PDFs conforme especificação
- Geração e persistência de embeddings vetoriais
- Busca semântica funcional
- Respostas restritas ao contexto recuperado
- Estrutura de projeto conforme exigido
- Execução via CLI
- Repositório público com README explicativo

---

## Observações Finais

- O sistema não responde perguntas fora do contexto ingerido
- Não há uso de memória externa ou conhecimento prévio do modelo
- Todo o armazenamento vetorial ocorre no PostgreSQL com pgvector
- O projeto pode ser executado integralmente a partir das instruções deste README

---

## Autor

Alexandre Vinhadelli Papadópolis  
MBA em Inteligência Artificial – Full Cycle
