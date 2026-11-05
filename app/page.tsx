
"use client";

import { useEffect, useState } from "react";
import {
  Bot,
  Plus,
  House,
  Sparkles,
  MessageCircle,
  Download,
  ArrowLeft,
  ArrowRight,
  Settings2,
  Trash2,
  Wifi,
  Laptop,
  Check,
  Send,
  Pencil,
  Eye,
  EyeOff,
} from "lucide-react";

// ======================================================
// TIPOS
// ======================================================

type Agent = {
  id: string;
  name: string;
  purpose: string;
  tone: string;
  instructions: string;
  createdAt: string;
};

type Screen =
  | "home"
  | "choose"
  | "guided"
  | "manual"
  | "review"
  | "chat"
  | "export"
  | "connection";

type Provider = "gemini" | "openai" | "anthropic" | "llama";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
};

// ======================================================
// CONFIGURAÇÕES
// ======================================================

const purposes = [
  "Analisar documentos",
  "Criar relatórios e KPIs",
  "Produzir conteúdo",
  "Organizar tarefas",
  "Outra finalidade",
];

const tones = [
  "Profissional e objetivo",
  "Amigável e descontraído",
  "Didático e detalhado",
];

const initial: Agent = {
  id: "",
  name: "",
  purpose: "",
  tone: tones[0],
  instructions: "",
  createdAt: "",
};

const prompts = [
  "Qual tarefa você quer facilitar?",
  "Qual nome você gostaria de dar ao agente?",
  "Como ele deve se comunicar?",
];

const hints = [
  "Ex.: Analisar relatórios e identificar tendências",
  "Ex.: Analista Inteligente",
  "Escolha abaixo ou descreva outro estilo",
];

const providerNames: Record<Provider, string> = {
  gemini: "Google Gemini",
  openai: "OpenAI (ChatGPT)",
  anthropic: "Anthropic (Claude)",
  llama: "Llama (Local)",
};

// ======================================================
// FUNÇÕES AUXILIARES
// ======================================================

const makeInstructions = (agent: Agent) =>
  `Você é um agente de IA chamado ${agent.name || "Meu Agente"}.
Sua principal função é: ${
    agent.purpose || "auxiliar o usuário em suas atividades"
  }.
Adote um tom ${agent.tone.toLowerCase()}.
Responda de forma clara e útil. Quando não souber uma resposta, informe suas limitações. Não invente informações.`;

function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `agent-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 11)}`;
}

// ======================================================
// COMPONENTE PRINCIPAL
// ======================================================

export default function Home() {
  // Navegação
  const [screen, setScreen] = useState<Screen>("home");

  // Agentes
  const [agents, setAgents] = useState<Agent[]>([]);
  const [draft, setDraft] = useState<Agent>(initial);
  const [selected, setSelected] = useState<string | null>(null);

  // Criação guiada
  const [step, setStep] = useState(0);
  const [answer, setAnswer] = useState("");

  // Chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  // Provedor de IA
  const [provider, setProvider] = useState<Provider>("gemini");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  // Ambiente
  const [endpoint, setEndpoint] = useState("");
  const [token, setToken] = useState("");
  const [connectionStatus, setConnectionStatus] = useState("");

  // Persistência
  const [hydrated, setHydrated] = useState(false);

  // ====================================================
  // CARREGAMENTO DOS AGENTES
  // ====================================================

  useEffect(() => {
    try {
      const savedAgents = JSON.parse(
        localStorage.getItem("agentlab-agents") || "[]"
      );

      setAgents(savedAgents);
    } catch {
      setAgents([]);
    }

    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) {
      localStorage.setItem(
        "agentlab-agents",
        JSON.stringify(agents)
      );
    }
  }, [agents, hydrated]);

  const active = agents.find((agent) => agent.id === selected);

  // ====================================================
  // CRIAÇÃO DE AGENTE
  // ====================================================

  function start(mode: "guided" | "manual") {
    setDraft({ ...initial });
    setStep(0);
    setAnswer("");

    setProvider("gemini");
    setApiKey("");
    setShowApiKey(false);

    setScreen(mode);
  }

  function nextGuided() {
    const value = answer.trim();

    if (!value) return;

    if (step === 0) {
      setDraft((current) => ({
        ...current,
        purpose: value,
      }));
    }

    if (step === 1) {
      setDraft((current) => ({
        ...current,
        name: value,
      }));
    }

    if (step === 2) {
      setDraft((current) => ({
        ...current,
        tone: value,
      }));
    }

    setAnswer("");

    if (step === 2) {
      setScreen("review");
    } else {
      setStep((current) => current + 1);
    }
  }

  function saveAgent() {
    const agent: Agent = {
      ...draft,
      id: draft.id || generateId(),
      createdAt: draft.createdAt || new Date().toISOString(),
      instructions:
        draft.instructions.trim() || makeInstructions(draft),
    };

    setAgents((previous) => [
      agent,
      ...previous.filter((item) => item.id !== agent.id),
    ]);

    setSelected(agent.id);
    setMessages([]);
    setScreen("chat");
  }

  // ====================================================
  // EXPORTAÇÃO
  // ====================================================

  function exportAgent() {
    const agent = active || draft;

    const blob = new Blob(
      [
        JSON.stringify(
          {
            schemaVersion: 1,
            name: agent.name,
            purpose: agent.purpose,
            tone: agent.tone,
            instructions: agent.instructions,
          },
          null,
          2
        ),
      ],
      {
        type: "application/json",
      }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;

    link.download = `${
      (agent.name || "meu-agente")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
    }.json`;

    link.click();
    URL.revokeObjectURL(url);
  }

  // ====================================================
  // CHAT
  // ====================================================

  async function sendMessage() {
    const text = chatInput.trim();

    if (!text || !active || isSending) return;

    const history = messages.map((message) => ({
      role: message.role,
      content: message.text,
    }));

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        text,
      },
    ]);

    setChatInput("");
    setIsSending(true);

    try {
      const response = await fetch("/api/agents/chat", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          agent: {
            id: active.id,
            name: active.name,
            purpose: active.purpose,
            tone: active.tone,
            instructions: active.instructions,
            rag_enabled: true,
            top_k: 4,
          },

          message: text,
          history,

          provider,

          api_key:
            provider === "llama"
              ? null
              : apiKey.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Erro ao executar o agente."
        );
      }

      const resposta = data.sources?.length
        ? `${data.response}\n\nFontes consultadas:\n${data.sources.join(
            "\n"
          )}`
        : data.response;

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: resposta,
        },
      ]);
    } catch (error) {
      const mensagem =
        error instanceof Error
          ? error.message
          : "Não foi possível executar o agente.";

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: `Erro: ${mensagem}`,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  // ====================================================
  // INTERFACE
  // ====================================================

  return (
    <div className="shell">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            <Sparkles size={22} />
          </div>

          <div>
            <strong>AgentLab</strong>
            <small>WORK INTELLIGENCE SUMMIT</small>
          </div>
        </div>

        <div className="nav">

          <button
            className={screen === "home" ? "active" : ""}
            onClick={() => setScreen("home")}
          >
            <House size={19} />
            Início
          </button>

          <button onClick={() => setScreen("home")}>
            <Bot size={19} />
            Meus agentes
            <span className="nav-count">{agents.length}</span>
          </button>

          <button
            className={
              ["choose", "guided", "manual", "review"].includes(
                screen
              )
                ? "active"
                : ""
            }
            onClick={() => setScreen("choose")}
          >
            <Plus size={19} />
            Criar agente
          </button>

          <button
            className={screen === "connection" ? "active" : ""}
            onClick={() => setScreen("connection")}
          >
            <Wifi size={19} />
            Ambiente
          </button>

        </div>

        <div className="sidebar-bottom">
          <span className="status-dot" />
          Protótipo do workshop
          <small>v0.1 · Interface demonstrativa</small>
        </div>

      </aside>

      {/* CONTEÚDO PRINCIPAL */}

      <main className="main">

        <header className="topbar">

          <div className="mobile-brand">
            <Sparkles size={18} />
            AgentLab
          </div>

          <span className="event-label">
            WORK INTELLIGENCE SUMMIT
          </span>

          <span className="pill">
            <span className="status-dot" />
            Ambiente conectado
          </span>

        </header>

        <div className="content">

          {/* ============================================
              HOME
          ============================================ */}

          {screen === "home" && (
            <>
              <section className="hero">

                <div className="eyebrow">
                  <Sparkles size={15} />
                  SEU LABORATÓRIO DE IA
                </div>

                <h1>
                  Suas ideias.
                  <br />
                  <span>Seu agente de IA.</span>
                </h1>

                <p>
                  Crie, personalize e experimente agentes de
                  inteligência artificial. Sem precisar escrever
                  uma linha de código.
                </p>

                <button
                  className="primary"
                  onClick={() => setScreen("choose")}
                >
                  <Plus size={18} />
                  Criar meu agente
                  <ArrowRight size={18} />
                </button>

                <div className="hero-orb">
                  <Bot size={72} />
                </div>

              </section>

              <div className="section-heading">

                <div>
                  <h2>Meus agentes</h2>
                  <p>
                    Continue de onde parou ou comece algo novo.
                  </p>
                </div>

                <span className="counter">
                  {agents.length} agente(s)
                </span>

              </div>

              <div className="agent-grid">

                {agents.map((agent) => (
                  <article
                    className="agent-card"
                    key={agent.id}
                  >
                    <div className="agent-avatar">
                      <Bot size={26} />
                    </div>

                    <h3>{agent.name}</h3>

                    <p>{agent.purpose}</p>

                    <div className="card-actions">

                      <button
                        className="secondary"
                        onClick={() => {
                          setSelected(agent.id);
                          setMessages([]);
                          setScreen("chat");
                        }}
                      >
                        Conversar
                        <ArrowRight size={16} />
                      </button>

                      <button
                        className="icon-button"
                        aria-label={`Excluir ${agent.name}`}
                        onClick={() => {
                          if (confirm(`Excluir ${agent.name}?`)) {
                            setAgents((previous) =>
                              previous.filter(
                                (item) => item.id !== agent.id
                              )
                            );

                            if (selected === agent.id) {
                              setSelected(null);
                              setMessages([]);
                              setScreen("home");
                            }
                          }
                        }}
                      >
                        <Trash2 size={17} />
                      </button>

                    </div>
                  </article>
                ))}

                <button
                  className="new-card"
                  onClick={() => setScreen("choose")}
                >
                  <div className="plus-circle">
                    <Plus size={23} />
                  </div>

                  <strong>Novo agente</strong>
                  <span>Comece com uma ideia</span>
                </button>

              </div>
            </>
          )}

          {/* ============================================
              ESCOLHER TIPO DE CRIAÇÃO
          ============================================ */}

          {screen === "choose" && (
            <div className="narrow">

              <button
                className="back"
                onClick={() => setScreen("home")}
              >
                <ArrowLeft size={17} />
                Voltar
              </button>

              <div className="eyebrow">CRIAR AGENTE</div>

              <h1>Como vamos começar?</h1>

              <p className="lead">
                Escolha a maneira mais confortável de construir
                seu assistente.
              </p>

              <div className="choice-grid">

                <button
                  className="choice"
                  onClick={() => start("guided")}
                >
                  <div className="choice-icon">
                    <MessageCircle />
                  </div>

                  <span className="badge">RECOMENDADO</span>

                  <h3>Criação guiada</h3>

                  <p>
                    Responda algumas perguntas e nós montamos
                    as instruções do seu agente.
                  </p>

                  <strong>
                    Começar
                    <ArrowRight size={16} />
                  </strong>
                </button>

                <button
                  className="choice"
                  onClick={() => start("manual")}
                >
                  <div className="choice-icon">
                    <Settings2 />
                  </div>

                  <h3>Configuração manual</h3>

                  <p>
                    Defina nome, objetivo, estilo e instruções
                    diretamente.
                  </p>

                  <strong>
                    Configurar
                    <ArrowRight size={16} />
                  </strong>
                </button>

              </div>
            </div>
          )}

          {/* ============================================
              CRIAÇÃO GUIADA
          ============================================ */}

          {screen === "guided" && (
            <div className="narrow">

              <button
                className="back"
                onClick={() => setScreen("choose")}
              >
                <ArrowLeft size={17} />
                Voltar
              </button>

              <div className="step-row">
                <span>CRIANDO SEU AGENTE</span>
                <span>Etapa {step + 1} de 3</span>
              </div>

              <div className="progress">
                <span
                  style={{
                    width: `${((step + 1) / 3) * 100}%`,
                  }}
                />
              </div>

              <div className="guide-bot">
                <Bot size={30} />
              </div>

              <h1>{prompts[step]}</h1>

              <p className="lead">{hints[step]}</p>

              {step === 0 && (
                <div className="suggestions">
                  {purposes.map((purpose) => (
                    <button
                      key={purpose}
                      onClick={() => setAnswer(purpose)}
                      className={
                        answer === purpose ? "selected" : ""
                      }
                    >
                      {purpose}
                    </button>
                  ))}
                </div>
              )}

              {step === 2 && (
                <div className="suggestions">
                  {tones.map((tone) => (
                    <button
                      key={tone}
                      onClick={() => setAnswer(tone)}
                      className={
                        answer === tone ? "selected" : ""
                      }
                    >
                      {tone}
                    </button>
                  ))}
                </div>
              )}

              <label
                className="field-label"
                htmlFor="guided-answer"
              >
                Sua resposta
              </label>

              <input
                id="guided-answer"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && nextGuided()
                }
                placeholder="Digite sua resposta..."
              />

              <button
                className="primary full"
                disabled={!answer.trim()}
                onClick={nextGuided}
              >
                Continuar
                <ArrowRight size={17} />
              </button>

            </div>
          )}

          {/* ============================================
              CONFIGURAÇÃO MANUAL
          ============================================ */}

          {screen === "manual" && (
            <div className="narrow">

              <button
                className="back"
                onClick={() => setScreen("choose")}
              >
                <ArrowLeft size={17} />
                Voltar
              </button>

              <div className="eyebrow">
                CONFIGURAÇÃO MANUAL
              </div>

              <h1>Personalize seu agente</h1>

              <p className="lead">
                Defina como seu agente deve agir e responder.
              </p>

              <div className="form-card">

                <label>
                  Nome do agente

                  <input
                    value={draft.name}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        name: e.target.value,
                      })
                    }
                    placeholder="Ex.: Analista Inteligente"
                  />
                </label>

                <label>
                  Objetivo principal

                  <input
                    value={draft.purpose}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        purpose: e.target.value,
                      })
                    }
                    placeholder="Ex.: Analisar relatórios"
                  />
                </label>

                <label>
                  Tom de voz

                  <select
                    value={draft.tone}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        tone: e.target.value,
                      })
                    }
                  >
                    {tones.map((tone) => (
                      <option key={tone}>{tone}</option>
                    ))}
                  </select>
                </label>

                <label>
                  Instruções adicionais (opcional)

                  <textarea
                    rows={5}
                    value={draft.instructions}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        instructions: e.target.value,
                      })
                    }
                    placeholder="Você é um agente que..."
                  />
                </label>

              </div>

              <button
                className="primary full"
                disabled={
                  !draft.name.trim() || !draft.purpose.trim()
                }
                onClick={() => setScreen("review")}
              >
                Revisar agente
                <ArrowRight size={17} />
              </button>

            </div>
          )}

          {/* ============================================
              REVISÃO E SELEÇÃO DO PROVEDOR
          ============================================ */}

          {screen === "review" && (
            <div className="narrow">

              <button
                className="back"
                onClick={() => setScreen("guided")}
              >
                <ArrowLeft size={17} />
                Voltar
              </button>

              <div className="eyebrow">QUASE LÁ</div>

              <h1>Seu agente está tomando forma ✨</h1>

              <p className="lead">
                Confira as instruções e escolha o modelo de
                inteligência artificial.
              </p>

              <div className="review-card">

                <div className="review-head">

                  <div className="agent-avatar">
                    <Bot />
                  </div>

                  <div>
                    <h3>{draft.name}</h3>
                    <p>{draft.purpose}</p>
                  </div>

                </div>

                <label>
                  Instruções do agente

                  <textarea
                    rows={11}
                    value={
                      draft.instructions ||
                      makeInstructions(draft)
                    }
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        instructions: e.target.value,
                      })
                    }
                  />
                </label>

              </div>

              {/* SELEÇÃO DO PROVEDOR */}

              <div className="form-card">

                <label htmlFor="provider">
                  Modelo de inteligência artificial
                </label>

                <select
                  id="provider"
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value as Provider);
                    setApiKey("");
                    setShowApiKey(false);
                  }}
                >
                  <option value="gemini">
                    Google Gemini
                  </option>

                  <option value="openai">
                    OpenAI (ChatGPT)
                  </option>

                  <option value="anthropic">
                    Anthropic (Claude)
                  </option>

                  <option value="llama">
                    Llama (Local)
                  </option>
                </select>

                {provider !== "llama" && (
                  <>
                    <label
                      htmlFor="api-key"
                      style={{ marginTop: "18px" }}
                    >
                      Chave de API
                    </label>

                    <div className="api-key-field">

                      <input
                        id="api-key"
                        type={
                          showApiKey ? "text" : "password"
                        }
                        value={apiKey}
                        onChange={(e) =>
                          setApiKey(e.target.value)
                        }
                        placeholder={
                          provider === "gemini"
                            ? "Cole sua chave do Google Gemini"
                            : provider === "openai"
                            ? "Cole sua chave da OpenAI"
                            : "Cole sua chave da Anthropic"
                        }
                        autoComplete="off"
                      />

                      <button
                        type="button"
                        className="icon-button"
                        onClick={() =>
                          setShowApiKey((previous) => !previous)
                        }
                        aria-label={
                          showApiKey
                            ? "Ocultar chave"
                            : "Mostrar chave"
                        }
                      >
                        {showApiKey ? (
                          <EyeOff size={18} />
                        ) : (
                          <Eye size={18} />
                        )}
                      </button>

                    </div>
                  </>
                )}

                <p className="lead">
                  {provider === "llama"
                    ? "O agente utilizará o modelo Llama configurado no backend. Nenhuma chave de API é necessária."
                    : `A chave será utilizada pelo ${providerNames[provider]}. Ela não será salva junto ao agente nem incluída na exportação. Se deixar em branco, o backend tentará utilizar a chave configurada no arquivo .env.`}
                </p>

              </div>

              <button
                className="primary full"
                onClick={saveAgent}
              >
                <Check size={18} />
                Criar e testar agente
              </button>

            </div>
          )}

          {/* ============================================
              CHAT
          ============================================ */}

          {screen === "chat" && active && (
            <div className="chat-layout">

              <div className="chat-header">

                <div className="agent-avatar small">
                  <Bot size={21} />
                </div>

                <div>
                  <h2>{active.name}</h2>
                  <p>{active.purpose}</p>
                </div>

                <button
                  className="secondary"
                  onClick={() => {
                    setDraft(active);
                    setScreen("manual");
                  }}
                >
                  <Pencil size={16} />
                  Editar
                </button>

                <button
                  className="secondary"
                  onClick={() => setScreen("export")}
                >
                  <Download size={16} />
                  Exportar
                </button>

              </div>

              <div className="messages">

                {messages.length === 0 ? (
                  <div className="empty-chat">

                    <div className="guide-bot">
                      <Bot size={32} />
                    </div>

                    <h2>Olá! Sou {active.name}.</h2>

                    <p>
                      Seu agente está configurado.
                      Faça uma pergunta para começar a conversar.
                    </p>

                    <div className="notice">
                      Provedor selecionado:{" "}
                      {providerNames[provider]}.
                      Envie uma mensagem para começar.
                    </div>

                  </div>
                ) : (
                  messages.map((message, index) => (
                    <div
                      className={`message ${message.role}`}
                      key={index}
                    >
                      {message.text}
                    </div>
                  ))
                )}

                {isSending && (
                  <div className="message assistant">
                    Gerando resposta...
                  </div>
                )}

              </div>

              <form
                className="chat-compose"
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
              >

                <input
                  aria-label="Mensagem"
                  placeholder="Pergunte alguma coisa..."
                  value={chatInput}
                  onChange={(e) =>
                    setChatInput(e.target.value)
                  }
                  disabled={isSending}
                />

                <button
                  className="send"
                  type="submit"
                  disabled={
                    !chatInput.trim() || isSending
                  }
                  aria-label="Enviar"
                >
                  {isSending ? (
                    "..."
                  ) : (
                    <Send size={19} />
                  )}
                </button>

              </form>

            </div>
          )}

          {/* ============================================
              EXPORTAÇÃO
          ============================================ */}

          {screen === "export" && active && (
            <div className="narrow">

              <button
                className="back"
                onClick={() => setScreen("chat")}
              >
                <ArrowLeft size={17} />
                Voltar ao chat
              </button>

              <div className="eyebrow">
                LEVE SEU AGENTE COM VOCÊ
              </div>

              <h1>Seu agente, suas regras.</h1>

              <p className="lead">
                Baixe as instruções e prepare-se para executar
                o agente no seu próprio ambiente.
              </p>

              <div className="form-card">

                <div className="review-head">

                  <div className="agent-avatar">
                    <Download />
                  </div>

                  <div>
                    <h3>{active.name}.json</h3>
                    <p>Configuração do agente · JSON</p>
                  </div>

                </div>

                <button
                  className="primary full"
                  onClick={exportAgent}
                >
                  <Download size={18} />
                  Baixar configuração
                </button>

              </div>

              <div className="notice">
                O arquivo exporta as instruções, não o modelo
                de IA nem as chaves de API. A estrutura de
                execução local será disponibilizada
                separadamente pela organização.
              </div>

              <button
                className="secondary"
                onClick={() => setScreen("connection")}
              >
                <Laptop size={17} />
                Configurar ambiente local
              </button>

            </div>
          )}

          {/* ============================================
              AMBIENTE
          ============================================ */}

          {screen === "connection" && (
            <div className="narrow">

              <button
                className="back"
                onClick={() => setScreen("home")}
              >
                <ArrowLeft size={17} />
                Voltar
              </button>

              <div className="eyebrow">
                AMBIENTE DE EXECUÇÃO
              </div>

              <h1>Conecte seu ambiente</h1>

              <p className="lead">
                No futuro, você poderá usar um endpoint seguro
                para acessar seus agentes executados localmente.
              </p>

              <div className="form-card">

                <label>
                  Endpoint HTTPS

                  <input
                    type="url"
                    value={endpoint}
                    onChange={(e) =>
                      setEndpoint(e.target.value)
                    }
                    placeholder="https://seu-endpoint.exemplo"
                  />
                </label>

                <label>
                  Token de acesso

                  <input
                    type="password"
                    value={token}
                    onChange={(e) =>
                      setToken(e.target.value)
                    }
                    placeholder="Token do ambiente"
                  />
                </label>

                <button
                  className="primary full"
                  onClick={() =>
                    setConnectionStatus(
                      "Esta tela é apenas um protótipo. Nenhuma conexão foi realizada."
                    )
                  }
                >
                  Testar conexão
                  <Wifi size={17} />
                </button>

                {connectionStatus && (
                  <div className="notice">
                    {connectionStatus}
                  </div>
                )}

              </div>

              <div className="notice">
                Não exponha APIs locais sem autenticação e HTTPS.
                Tokens digitados aqui não são armazenados nem
                enviados nesta versão.
              </div>

            </div>
          )}

        </div>
      </main>

      {/* NAVEGAÇÃO MOBILE */}

      <nav className="mobile-nav">

        <button onClick={() => setScreen("home")}>
          <House size={20} />
          <span>Início</span>
        </button>

        <button onClick={() => setScreen("home")}>
          <Bot size={20} />
          <span>Agentes</span>
        </button>

        <button onClick={() => setScreen("choose")}>
          <Plus size={20} />
          <span>Criar</span>
        </button>

        <button onClick={() => setScreen("connection")}>
          <Wifi size={20} />
          <span>Ambiente</span>
        </button>

      </nav>

    </div>
  );
}
