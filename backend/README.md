# Gerador de Posts (RAG + LoRA + Gemini)

Sistema de geração de posts para redes sociais utilizando **Retrieval-Augmented Generation (RAG)**, fine-tuning com **LoRA** e integração com a **API do Google Gemini**.

O projeto permite alternar entre um modelo Llama executado localmente, com ou sem adaptador LoRA, e um modelo Gemini acessado via API.

## Arquitetura

**Fluxo offline:**

PDFs → Chunking → Embeddings → ChromaDB

**Fluxo online:**

Tema → Retriever (Top-K) → Prompt (contexto + instruções) → LLM → Validação → Revisão humana

**Provedores de LLM disponíveis:**

- **Llama + LoRA:** execução local utilizando Transformers, PyTorch e PEFT.
- **Gemini API:** geração remota utilizando o SDK oficial `google-genai`.

## Módulos

| Arquivo | Responsabilidade |
|---|---|
| `config.py` | Parâmetros e configurações de todas as etapas |
| `embeddings.py` | Modelo de embeddings compartilhado entre indexação e consulta |
| `index.py` | Processamento dos PDFs, chunking, embeddings e armazenamento no ChromaDB (offline) |
| `retriever.py` | Recuperação dos documentos relevantes (Top-K) |
| `prompt.py` | Construção do prompt com contexto, instruções e tom de comunicação |
| `llm.py` | Gerenciamento dos provedores Llama + LoRA e Gemini API |
| `validate.py` | Validação e formatação das respostas geradas |
| `pipeline.py` | Orquestração das etapas online do RAG |
| `main.py` | Interface de execução, revisão humana e armazenamento de exemplos |
| `train_lora.py` | Fine-tuning LoRA utilizando exemplos aprovados (offline) |

## Tecnologias

- **Linguagem:** Python
- **RAG:** LangChain e ChromaDB
- **Embeddings:** Sentence Transformers
- **LLM local:** Transformers e PyTorch
- **Fine-tuning:** PEFT (LoRA)
- **LLM via API:** Google Gemini (`google-genai`)
- **Interface:** CLI / aplicação web
- **Versionamento:** Git e GitHub

## Configuração inicial

### 1. Clonar o repositório

```bash
git clone https://github.com/dev-Burandelei/RAG_POST.git
cd RAG_POST
```

### 2. Criar e ativar o ambiente virtual

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

Para treinamento LoRA, instale também:

```bash
pip install -r requirements-treino.txt
```

### 4. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Provedor de LLM: llama ou gemini
LLM_PROVIDER=llama

# Configurações do Gemini
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash

# Parâmetros de geração
MAX_NOVOS_TOKENS=1024
TEMPERATURA=0.3
```

Para utilizar o Gemini, obtenha uma chave de API no [Google AI Studio](https://aistudio.google.com/apikey).

**Importante:** adicione `.env` ao `.gitignore`. Nunca compartilhe ou envie sua chave de API ao GitHub.

## Execução

### 1. Preparar a base de conhecimento

Coloque os arquivos PDF na pasta `base/` e execute:

```bash
python index.py
```

O processo realiza:

1. Leitura dos documentos.
2. Divisão em chunks.
3. Geração dos embeddings.
4. Armazenamento dos vetores no ChromaDB (`db/`).

Essa etapa é executada novamente sempre que houver alterações relevantes na base de documentos ou na configuração de indexação.

### 2. Testar a recuperação

Antes de gerar posts, valide a recuperação dos documentos:

```bash
python retriever.py "tema do post"
```

O retriever realiza a busca semântica e retorna os documentos mais relevantes para o tema informado.

### 3. Selecionar o modelo de geração

A escolha do provedor é feita pela variável `LLM_PROVIDER` no arquivo `.env`.

**Opção A — Llama local**

```env
LLM_PROVIDER=llama
```

Para utilizar o modelo base sem adaptador LoRA:

```bash
python main.py --sem-lora
```

Para utilizar o modelo com o adaptador treinado:

```bash
python main.py
```

O adaptador é carregado a partir de `adapters/instagram/`, quando disponível.

**Opção B — Gemini API**

```env
LLM_PROVIDER=gemini
```

Execute:

```bash
python main.py
```

A geração será realizada pela API do Gemini, sem necessidade de carregar o modelo localmente.

> **Observação:** o adaptador LoRA treinado para o Llama não é compatível com o Gemini. A opção `--sem-lora` não é necessária quando o provedor selecionado é o Gemini.

### 4. Revisão humana

Após a geração:

1. Analise o conteúdo produzido.
2. Aprove ou edite as respostas.
3. Armazene os exemplos aprovados em `data/exemplos.jsonl`.

Esses exemplos formarão a base para futuras etapas de fine-tuning.

### 5. Treinamento LoRA

Após acumular algumas dezenas de exemplos revisados, instale as dependências de treinamento:

```bash
pip install -r requirements-treino.txt
```

Execute:

```bash
python train_lora.py
```

O treinamento gera o adaptador LoRA, armazenado em:

```text
adapters/
└── instagram/
```

Para utilizar o adaptador, selecione `LLM_PROVIDER=llama` no `.env` e execute:

```bash
python main.py
```

**Importante:** o treinamento LoRA é realizado para o modelo Llama configurado no projeto. Caso o modelo base seja alterado, será necessário verificar a compatibilidade do adaptador e, normalmente, realizar um novo treinamento.

## Regras e boas práticas

- **Embeddings:** se o modelo de embeddings mudar, apague a pasta `db/` e execute novamente `python index.py`.
- **Chunking:** alterações no tamanho dos chunks ou na sobreposição também exigem a reconstrução do índice.
- **Prompt:** alterações no `SYSTEM_PROMPT` em `prompt.py` devem ser avaliadas. Se modificarem significativamente o comportamento esperado, revise os exemplos e considere retreinar o LoRA.
- **LoRA:** o adaptador deve ser utilizado exclusivamente com o modelo base compatível com o treinamento.
- **Gemini:** requer conexão com a internet e uma chave de API válida.
- **Segurança:** nunca versione arquivos `.env`, credenciais ou dados sensíveis.
- **Revisão humana:** valide os conteúdos antes de utilizá-los ou publicá-los.

## Estrutura do projeto

```text
rag_posts/
│
├── adapters/
│   └── instagram/          # Adaptador LoRA treinado
│
├── base/                   # PDFs da base de conhecimento
│
├── data/
│   └── exemplos.jsonl      # Exemplos revisados
│
├── db/                     # Banco vetorial ChromaDB
│
├── .env                    # Variáveis de ambiente
├── .gitignore
├── config.py
├── embeddings.py
├── index.py
├── retriever.py
├── prompt.py
├── llm.py
├── validate.py
├── pipeline.py
├── main.py
├── train_lora.py
├── requirements.txt
└── requirements-treino.txt
```

## Objetivo do projeto

Desenvolver um sistema de geração de conteúdo contextualizado, capaz de recuperar informações de uma base documental própria e produzir posts alinhados ao tom e às diretrizes estabelecidas.

A arquitetura também permite comparar diferentes abordagens de geração, avaliando modelos locais com fine-tuning LoRA e modelos comerciais acessados por API, considerando qualidade das respostas, fidelidade ao contexto, latência e custos de execução.