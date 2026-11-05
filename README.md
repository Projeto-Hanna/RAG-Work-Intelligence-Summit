# AgentLab — Protótipo v0.1

Aplicação web responsiva desenvolvida para a oficina **Crie seu próprio agente de IA**, do Work Intelligence Summit.

O AgentLab permite criar, configurar e testar agentes de IA, selecionando diferentes provedores de modelos de linguagem (LLMs).

## Funcionalidades

- Dashboard responsivo e adaptado para dispositivos móveis.
- Criação guiada de agentes por meio de perguntas.
- Configuração manual de agentes, incluindo nome, propósito, tom e instruções.
- Revisão e edição das instruções dos agentes.
- Salvamento e exclusão de agentes no `localStorage` do navegador.
- Chat integrado ao backend para execução de conversas com modelos de IA.
- Seleção entre diferentes provedores de LLM.
- Suporte a Gemini, OpenAI, Anthropic e modelos locais via Llama.
- Configuração de API Key para provedores que exigem autenticação.
- Exportação da configuração dos agentes em JSON.

## Tecnologias

### Frontend
- Node.js 20.9+ (recomendado: Node.js 22).
- Next.js 15.
- React 19.
- TypeScript.
- npm.

### Backend
- Python 3.10+.
- FastAPI.
- Uvicorn.
- Integrações com os provedores de LLM.
- ChromaDB e modelos de embeddings para funcionalidades de RAG.

## Pré-requisitos

- Node.js 20.9 ou superior.
- npm.
- Python 3.10 ou superior.
- Ambiente virtual Python configurado.
- Chaves de API dos provedores que exigem autenticação.

## Executar localmente

O frontend e o backend são iniciados simultaneamente por meio de um único comando.

### 1. Instalar dependências do frontend

Na raiz do projeto:

```bash
npm install
```

### 2. Configurar o ambiente Python

Acesse a pasta do backend:

```bash
cd backend
```

Crie e ative o ambiente virtual, caso ainda não exista:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Retorne à raiz do projeto:

```bash
cd ..
```

### 3. Configurar variáveis de ambiente

Configure os arquivos `.env` conforme as variáveis esperadas pelo backend e pelo frontend.

No backend, configure as chaves e os modelos dos provedores que deseja utilizar.

No frontend, configure a URL do backend quando necessário:

```env
BACKEND_URL=http://127.0.0.1:8000
```

**Importante:** não compartilhe nem versione arquivos `.env` com chaves de API. As credenciais devem ser mantidas em ambiente seguro.

### 4. Iniciar a aplicação

Na raiz do projeto:

```bash
npm run dev
```

O comando inicia os dois serviços:

| Serviço | Endereço |
|---|---|
| Frontend — Next.js | http://localhost:3000 |
| Backend — FastAPI | http://127.0.0.1:8000 |

Para encerrar os serviços, pressione `Ctrl + C` no terminal.

## Provedores de IA

O AgentLab possui integração com os seguintes provedores:

| Provedor | Identificador |
|---|---|
| Google Gemini | `gemini` |
| OpenAI | `openai` |
| Anthropic | `anthropic` |
| Llama | `llama` |

A disponibilidade de cada modelo depende da configuração, das credenciais e do acesso ao serviço correspondente.

As API Keys informadas para uso na aplicação não devem ser armazenadas junto às configurações dos agentes no `localStorage`.

## Armazenamento de dados

Atualmente, as configurações dos agentes são armazenadas no navegador por meio do `localStorage`.

Isso significa que:
- Os agentes ficam disponíveis no navegador em que foram criados.
- Os dados não são sincronizados automaticamente entre dispositivos.
- A limpeza dos dados do navegador pode apagar as configurações salvas.
- A exportação em JSON permite preservar as configurações dos agentes.

## Publicação

### Frontend — Vercel

1. Envie o projeto para um repositório Git.
2. Importe o repositório na Vercel.
3. Configure o projeto como uma aplicação Next.js.
4. Defina a variável `BACKEND_URL` apontando para o endereço público do backend.
5. Execute o deploy.

### Backend

O backend FastAPI precisa ser hospedado separadamente em um serviço compatível com Python.

Após a publicação, configure:
- URL pública do backend.
- Variáveis de ambiente.
- Credenciais dos provedores de IA.
- Dependências e recursos necessários para execução do RAG.

**Atenção:** o endereço `127.0.0.1` é válido apenas para execução local. Em produção, o frontend deve apontar para o endereço público do backend, com comunicação HTTPS e medidas adequadas de autenticação e proteção das credenciais.

## Limitações atuais

- Autenticação de usuários ainda não implementada.
- Persistência dos agentes limitada ao `localStorage`.
- Sincronização entre dispositivos não implementada.
- Upload de documentos e gerenciamento de bases de conhecimento ainda em desenvolvimento.
- Segurança de produção, incluindo autenticação e gerenciamento de credenciais, requer implementação e validação adicionais.

## Próximas etapas

1. Definir e documentar o contrato JSON e a API do runtime.
2. Implementar autenticação e comunicação segura via HTTPS.
3. Persistir agentes por usuário em um banco de dados.
4. Implementar importação e gerenciamento de configurações.
5. Expandir o upload de documentos e as funcionalidades de RAG.
6. Melhorar o gerenciamento de contexto e histórico das conversas.
7. Testar navegação mobile, acessibilidade e segurança.
8. Preparar a aplicação para publicação em ambiente de produção.

---

**AgentLab — Work Intelligence Summit**