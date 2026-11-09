# AgentLab — Plataforma de Agentes de IA com RAG

Plataforma para criação e gerenciamento de agentes de inteligência artificial, com integração a diferentes provedores de LLM e sistemas de Retrieval-Augmented Generation (RAG).

O **AgentLab** permite configurar agentes com instruções próprias, conectar bases de conhecimento documentais e gerar respostas contextualizadas a partir de informações recuperadas por busca semântica.

A arquitetura combina uma interface web, uma API em Python, armazenamento relacional de metadados e bancos vetoriais independentes para gerenciamento do conhecimento de cada agente.

## Arquitetura

O sistema é dividido em duas camadas principais:

### Frontend

Aplicação web desenvolvida com Next.js, React e TypeScript, responsável pela interface de gerenciamento e interação com os agentes.

### Backend

API desenvolvida com FastAPI e Python, responsável pela execução dos agentes, processamento documental, recuperação de contexto e integração com os provedores de modelos de linguagem.

### Fluxo de processamento documental

```text
Upload de documentos
        ↓
Validação e armazenamento
        ↓
Extração do conteúdo
        ↓
Divisão em chunks
        ↓
Geração de embeddings
        ↓
Armazenamento no ChromaDB
```

### Fluxo de geração de respostas

```text
Pergunta do usuário
        ↓
Identificação do agente
        ↓
Retriever (busca semântica)
        ↓
Recuperação dos chunks relevantes
        ↓
Construção do prompt com contexto
        ↓
LLM
        ↓
Resposta contextualizada
```

## Principais funcionalidades

- **Gerenciamento de agentes:** criação, configuração e utilização de agentes com instruções específicas.
- **Múltiplos provedores de LLM:** integração com diferentes provedores, incluindo Gemini, OpenAI, Anthropic e modelos locais, conforme a configuração disponível.
- **RAG:** recuperação de informações relevantes em bases documentais para fundamentar as respostas.
- **Gerenciamento documental:** upload, listagem e exclusão de documentos associados aos agentes.
- **Indexação individual:** processamento e indexação de documentos de forma independente, sem exigir a reconstrução completa da base.
- **Reindexação:** atualização dos vetores de um documento já indexado.
- **Bases de conhecimento:** suporte a uma base compartilhada de testes e bases individuais por agente.
- **Persistência:** armazenamento de metadados e informações dos agentes em SQLite e vetores no ChromaDB.

## Gerenciamento das bases de conhecimento

O AgentLab trabalha com dois tipos de bases:

| Tipo | Descrição |
|---|---|
| `test` | Utiliza uma base de conhecimento compartilhada entre os agentes configurados nesse modo. |
| `custom` | Mantém uma base de conhecimento individual para cada agente. |

Na modalidade individual, cada agente possui seus próprios documentos e seu próprio banco vetorial.

O escopo de recuperação é utilizado para evitar que informações de uma base sejam recuperadas indevidamente por outra.

### Formatos de documentos suportados

- PDF
- CSV
- XLSX
- JSON

O limite de upload implementado é de 50 MB por arquivo.

## Tecnologias

| Categoria | Tecnologias |
|---|---|
| Linguagem | Python, TypeScript |
| Frontend | Next.js, React |
| Backend | FastAPI |
| Banco relacional | SQLite |
| Banco vetorial | ChromaDB |
| RAG | LangChain |
| Embeddings | Sentence Transformers |
| LLMs | Gemini, OpenAI, Anthropic e modelos locais |
| Versionamento | Git e GitHub |

## Estrutura do projeto

```text
RAG-Work-Intelligence-Summit/
│
├── app/
│   ├── api/
│   │   └── agents/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
│
├── backend/
│   ├── agent/
│   │   ├── executor.py
│   │   └── schemas.py
│   │
│   ├── api/
│   │   ├── agents.py
│   │   └── documents.py
│   │
│   ├── database/
│   │   └── agentlab.db
│   │
│   ├── data/
│   │   └── agents/
│   │
│   ├── config.py
│   ├── database.py
│   ├── embeddings.py
│   ├── index.py
│   ├── knowledge_base.py
│   ├── retriever.py
│   └── webapp.py
│
├── package.json
├── requirements.txt
└── README.md
```

## Configuração inicial

### 1. Clonar o repositório

```bash
git clone https://github.com/dev-Burandelei/RAG-Work-Intelligence-Summit.git
cd RAG-Work-Intelligence-Summit
```

### 2. Configurar o backend

Entre na pasta do backend:

```bash
cd backend
```

Crie e ative o ambiente virtual:

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente conforme os provedores de LLM habilitados no arquivo de configuração do projeto.

### 3. Configurar o frontend

Na raiz do projeto:

```bash
npm install
```

Configure as variáveis de ambiente necessárias para a comunicação entre o frontend e o backend.

## Execução

O AgentLab utiliza dois serviços: frontend e backend.

### 1. Iniciar o backend

Dentro da pasta `backend`, com o ambiente virtual ativado:

```bash
python -m uvicorn webapp:app --reload --host 127.0.0.1 --port 8000
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

A documentação interativa da API pode ser acessada em:

```text
http://127.0.0.1:8000/docs
```

### 2. Iniciar o frontend

Na raiz do projeto:

```bash
npm run dev
```

A aplicação ficará disponível em:

```text
http://localhost:3000
```

## Gerenciamento de documentos

Cada agente pode possuir documentos associados à sua base de conhecimento.

O gerenciamento é realizado pela interface ou pelos endpoints da API.

| Método | Endpoint | Responsabilidade |
|---|---|---|
| GET | `/api/agents/{agent_id}/documents` | Lista documentos do agente |
| POST | `/api/agents/{agent_id}/documents` | Envia documentos |
| DELETE | `/api/agents/{agent_id}/documents/{document_id}` | Exclui um documento |
| POST | `/api/agents/{agent_id}/documents/{document_id}/index` | Indexa ou reindexa um documento |

### Status dos documentos

Os documentos possuem estados de processamento que permitem acompanhar a indexação:

- `uploaded`: documento enviado e registrado.
- `processing`: documento em processamento.
- `indexed`: documento indexado com sucesso.
- `error`: ocorreu um erro durante o processamento.

A indexação individual permite atualizar o conteúdo de um documento sem executar a indexação completa de todos os arquivos da base.

## Recuperação de informações (RAG)

O mecanismo RAG utiliza embeddings para representar os documentos em formato vetorial.

Quando o usuário envia uma pergunta, o sistema:

1. Converte a consulta em uma representação vetorial.
2. Busca os chunks semanticamente relevantes.
3. Recupera o conteúdo associado à consulta.
4. Incorpora o contexto recuperado ao prompt.
5. Encaminha o prompt ao modelo de linguagem.
6. Retorna a resposta gerada pelo agente.

A separação por escopo das bases de conhecimento permite manter o isolamento entre os documentos dos diferentes agentes.

## Banco de dados

O projeto utiliza duas estratégias complementares de armazenamento:

**SQLite**

Responsável pelos dados estruturados, como:

- Cadastro e configuração dos agentes.
- Metadados dos documentos.
- Caminhos dos arquivos.
- Status de processamento.
- Informações de gerenciamento.

**ChromaDB**

Responsável pelo armazenamento dos embeddings e dos chunks utilizados na recuperação semântica.

Cada base individual possui seu próprio diretório de armazenamento vetorial.

## Segurança e boas práticas

- Não versione arquivos `.env` ou credenciais.
- Nunca exponha chaves de API no frontend ou no repositório.
- Preserve os bancos de dados e documentos utilizados pelo sistema.
- Mantenha o isolamento entre as bases de conhecimento dos agentes.
- Valide os arquivos enviados antes do processamento.
- Monitore os erros de indexação e recuperação.
- Utilize variáveis de ambiente para configurações sensíveis.

## Objetivo do projeto

Desenvolver uma plataforma modular de agentes inteligentes, capaz de combinar modelos de linguagem com bases documentais próprias por meio de RAG.

O AgentLab busca oferecer flexibilidade na escolha dos provedores de LLM, isolamento das bases de conhecimento, gerenciamento documental e recuperação contextualizada de informações.

A arquitetura permite evoluir para novos recursos, como avaliação de respostas, rastreabilidade das fontes recuperadas, observabilidade, otimização de prompts e treinamento especializado de modelos.
