
"use client";
import {
  saveCredential,
  getCredentialMetadata,
  unlockCredential,
} from "../lib/credential-vault";
import { useEffect, useState } from "react";
import {
  Bot,
  Plus,
  House,
  Files,
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
  LockKeyhole,
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
  provider: Provider;
  createdAt: string;
  knowledgeBaseType: "test" | "custom";
};

type Screen =
  | "home"
  | "choose"
  | "guided"
  | "manual"
  | "review"
  | "chat"
  | "export"
  | "documents"
  | "connection";

type Provider = "gemini" | "openai" | "anthropic" | "llama";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
};

type AgentDocument = {
  id: number;
  nome: string;
  status: string;
  data_criacao: string;
  tamanho: number;

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
  provider: "gemini",
  createdAt: "",
  knowledgeBaseType: "test",
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
const IDLE_TIMEOUT_MS = 15 * 60 * 1000;

function formatarTamanho(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatarData(data: string): string {
  const dataFormatada = new Date(data);

  if (Number.isNaN(dataFormatada.getTime())) {
    return data;
  }

  return dataFormatada.toLocaleString("pt-BR");
}

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

  // Documentos
  const [documents, setDocuments] = useState<AgentDocument[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [isUploadingDocuments, setIsUploadingDocuments] = useState(false);
  const [documentError, setDocumentError] = useState("");
  const [documentSuccess, setDocumentSuccess] = useState("");
  const [indexingDocumentId, setIndexingDocumentId] = useState<number | null>(null);

  async function carregarDocumentos(agentId: string) {
    setIsLoadingDocuments(true);
    setDocumentError("");

    try {
      const response = await fetch(
        `/api/agents/${agentId}/documents`,
        { cache: "no-store" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Erro ao carregar documentos."
        );
      }

      setDocuments(data.documentos || []);
    } catch (error) {
      setDocumentError(
        error instanceof Error
          ? error.message
          : "Não foi possível carregar os documentos."
      );
    } finally {
      setIsLoadingDocuments(false);
    }
  }

  async function enviarDocumentos(files: FileList | null) {
  if (!files || !active || files.length === 0) return;

  setIsUploadingDocuments(true);
  setDocumentError("");
  setDocumentSuccess("");

  try {
    const formData = new FormData();

    Array.from(files).forEach((file) => {
      formData.append("files", file);
    });

    const response = await fetch(
      `/api/agents/${active.id}/documents`,
      {
        method: "POST",
        body: formData,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Erro ao enviar documentos."
      );
    }

    setDocumentSuccess("Documentos enviados com sucesso!");
    await carregarDocumentos(active.id);
  } catch (error) {
    setDocumentError(
      error instanceof Error
        ? error.message
        : "Não foi possível enviar os documentos."
    );
  } finally {
    setIsUploadingDocuments(false);
  }
}

async function indexarDocumento(documentId: number) {
  if (!active || indexingDocumentId !== null) return;

  setIndexingDocumentId(documentId);
  setDocumentError("");
  setDocumentSuccess("");

  try {
    const response = await fetch(
      `/api/agents/${active.id}/documents/${documentId}/index`,
      { method: "POST" }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Erro ao indexar documento."
      );
    }

    setDocumentSuccess(
      `Documento "${data.document_id}" indexado com sucesso!`
    );

    await carregarDocumentos(active.id);
  } catch (error) {
    setDocumentError(
      error instanceof Error
        ? error.message
        : "Não foi possível indexar o documento."
    );

    await carregarDocumentos(active.id);
  } finally {
    setIndexingDocumentId(null);
  }
}

  // Provedor de IA
  const [provider, setProvider] = useState<Provider>("gemini");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);


  // Credenciais
  const [credentialPassword, setCredentialPassword] = useState("");
  const [showUnlockModal, setShowUnlockModal] = useState(false);
  const [unlockPassword, setUnlockPassword] = useState("");
  const [unlockError, setUnlockError] = useState("");
  const [pendingMessage, setPendingMessage] = useState("");
  const [unlockedCredentials, setUnlockedCredentials] = useState<Record<string, { provider: Provider; apiKey: string }>>({});
  const [credentialStatus, setCredentialStatus] = useState<Record<string, "unlocked" | "locked" | "missing" | "local">>({});
  const [lastActivityByAgent, setLastActivityByAgent] = useState<Record<string, number>>({});
  const [sessionNotice, setSessionNotice] = useState("");
  const [clockNow, setClockNow] = useState(Date.now());
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

  useEffect(() => {
    let cancelled = false;

    async function updateCredentialStatuses() {
      const statuses: Record<
        string,
        "unlocked" | "locked" | "missing" | "local"
      > = {};

      for (const agent of agents) {
        const agentProvider = agent.provider ?? "gemini";

        if (agentProvider === "llama") {
          statuses[agent.id] = "local";
          continue;
        }

        if (
          unlockedCredentials[agent.id]?.provider === agentProvider
        ) {
          statuses[agent.id] = "unlocked";
          continue;
        }

        const metadata = await getCredentialMetadata(agent.id);
        statuses[agent.id] = metadata ? "locked" : "missing";
      }

      if (!cancelled) {
        setCredentialStatus(statuses);
      }
    }

    updateCredentialStatuses();

    return () => {
      cancelled = true;
    };
  }, [agents, unlockedCredentials]);

// Atualiza o relógio a cada segundo
useEffect(() => {
  const interval = window.setInterval(() => {
    setClockNow(Date.now());
  }, 1000);

  return () => window.clearInterval(interval);
}, []);

// Controle de atividade e bloqueio automático por agente
useEffect(() => {
  const agentId = active?.id;

  const registerActivity = () => {
    if (!agentId || !unlockedCredentials[agentId]) return;

    setLastActivityByAgent((previous) => ({
      ...previous,
      [agentId]: Date.now(),
    }));
  };

  window.addEventListener("pointerdown", registerActivity);
  window.addEventListener("keydown", registerActivity);
  window.addEventListener("touchstart", registerActivity);
  window.addEventListener("wheel", registerActivity);

  const unlockedIds = Object.keys(unlockedCredentials);

  const expirationTimes = unlockedIds.map((id) => {
    const lastActivity = lastActivityByAgent[id] ?? Date.now();
    return lastActivity + IDLE_TIMEOUT_MS;
  });

  if (expirationTimes.length > 0) {
    const nextExpiration = Math.min(...expirationTimes);

    const timeout = window.setTimeout(() => {
      const now = Date.now();

      const expiredIds = Object.keys(unlockedCredentials).filter((id) => {
        const lastActivity = lastActivityByAgent[id] ?? now;
        return now - lastActivity >= IDLE_TIMEOUT_MS;
      });

      if (expiredIds.length > 0) {
        setUnlockedCredentials((previous) => {
          const updated = { ...previous };
          expiredIds.forEach((id) => delete updated[id]);
          return updated;
        });

        setLastActivityByAgent((previous) => {
          const updated = { ...previous };
          expiredIds.forEach((id) => delete updated[id]);
          return updated;
        });

        if (agentId && expiredIds.includes(agentId)) {
          setSessionNotice(
            "Credencial bloqueada por inatividade. Desbloqueie novamente para continuar."
          );
        }
      }
    }, Math.max(nextExpiration - Date.now(), 0));

    return () => {
      window.removeEventListener("pointerdown", registerActivity);
      window.removeEventListener("keydown", registerActivity);
      window.removeEventListener("touchstart", registerActivity);
      window.removeEventListener("wheel", registerActivity);
      window.clearTimeout(timeout);
    };
  }

  return () => {
    window.removeEventListener("pointerdown", registerActivity);
    window.removeEventListener("keydown", registerActivity);
    window.removeEventListener("touchstart", registerActivity);
    window.removeEventListener("wheel", registerActivity);
  };
}, [active?.id, unlockedCredentials, lastActivityByAgent]);

// Controle de atividade e bloqueio automático por agente
useEffect(() => {
    const agentId = active?.id;

    const registerActivity = () => {
      if (!agentId || !unlockedCredentials[agentId]) return;

      setLastActivityByAgent((previous) => ({
        ...previous,
        [agentId]: Date.now(),
      }));
    };

    window.addEventListener("pointerdown", registerActivity);
    window.addEventListener("keydown", registerActivity);
    window.addEventListener("touchstart", registerActivity);
    window.addEventListener("wheel", registerActivity);

    const unlockedIds = Object.keys(unlockedCredentials);

    const expirationTimes = unlockedIds.map((id) => {
      const lastActivity = lastActivityByAgent[id];
      return (lastActivity || Date.now()) + IDLE_TIMEOUT_MS;
    });

    if (expirationTimes.length > 0) {
      const nextExpiration = Math.min(...expirationTimes);

      const timeout = window.setTimeout(() => {
        const now = Date.now();

        const expiredIds = Object.keys(unlockedCredentials).filter((id) => {
          const lastActivity = lastActivityByAgent[id] || now;
          return now - lastActivity >= IDLE_TIMEOUT_MS;
        });

        if (expiredIds.length > 0) {
          setUnlockedCredentials((previous) => {
            const updated = { ...previous };
            expiredIds.forEach((id) => delete updated[id]);
            return updated;
          });

          setLastActivityByAgent((previous) => {
            const updated = { ...previous };
            expiredIds.forEach((id) => delete updated[id]);
            return updated;
          });

          if (agentId && expiredIds.includes(agentId)) {
            setSessionNotice(
              "Credencial bloqueada por inatividade. Desbloqueie novamente para continuar."
            );
          }
        }
      }, Math.max(nextExpiration - Date.now(), 0));

      return () => {
        window.removeEventListener("pointerdown", registerActivity);
        window.removeEventListener("keydown", registerActivity);
        window.removeEventListener("touchstart", registerActivity);
        window.removeEventListener("wheel", registerActivity);
        window.clearTimeout(timeout);
      };
    }

    return () => {
      window.removeEventListener("pointerdown", registerActivity);
      window.removeEventListener("keydown", registerActivity);
      window.removeEventListener("touchstart", registerActivity);
      window.removeEventListener("wheel", registerActivity);
    };
  }, [active?.id, unlockedCredentials, lastActivityByAgent]);
  // ====================================================
  // CRIAÇÃO DE AGENTE
  // ====================================================

  function start(mode: "guided" | "manual") {
    setDraft({ ...initial });
    setStep(0);
    setAnswer("");

    setProvider("gemini");
    setApiKey("");
    setCredentialPassword("");
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

async function saveAgent() {
  try {
    const agent: Agent = {
      ...draft,
      id: draft.id || generateId(),
      provider,
      createdAt: draft.createdAt || new Date().toISOString(),
      instructions:
        draft.instructions.trim() || makeInstructions(draft),
    };

    if (provider !== "llama") {
      if (!apiKey.trim()) {
        throw new Error("Informe a chave de API do provedor.");
      }

      if (credentialPassword.length < 12) {
        throw new Error(
          "A senha deve possuir pelo menos 12 caracteres."
        );
      }

      await saveCredential(
        agent.id,
        provider,
        apiKey,
        credentialPassword
      );
    }

    // Registra o agente no SQLite pelo backend.
    const response = await fetch("/api/agents/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        id: agent.id,
        name: agent.name,
        knowledge_base_type: agent.knowledgeBaseType,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "Não foi possível registrar o agente no banco."
      );
    }

    setAgents((previous) => [
      agent,
      ...previous.filter((item) => item.id !== agent.id),
    ]);

    setSelected(agent.id);
    setMessages([]);
    setApiKey("");
    setCredentialPassword("");
    setShowApiKey(false);
    setScreen("chat");
  } catch (error) {
    alert(
      error instanceof Error
        ? error.message
        : "Não foi possível salvar o agente."
    );
  }
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
  setLastActivityByAgent((previous) => ({
    ...previous,
    [active.id]: Date.now(),
  }));

setSessionNotice("");

  setIsSending(true);

  try {
    const agentProvider = active.provider ?? "gemini";

    if (agentProvider !== "llama") {
      const cachedCredential = unlockedCredentials[active.id];

      if (
        cachedCredential &&
        cachedCredential.provider === agentProvider
      ) {
        await executeMessage(text, cachedCredential.apiKey);
        return;
      }

      const metadata = await getCredentialMetadata(active.id);

      if (!metadata) {
        throw new Error(
          "Este agente não possui uma chave cadastrada. Edite o agente e cadastre novamente a chave e a senha."
        );
      }

      setPendingMessage(text);
      setUnlockPassword("");
      setUnlockError("");
      setShowUnlockModal(true);
      return;
    }

    await executeMessage(text, null);
  } catch (error) {
    const mensagem =
      error instanceof Error
        ? error.message
        : "Não foi possível preparar o envio.";

    setMessages((previous) => [
      ...previous,
      { role: "assistant", text: `Erro: ${mensagem}` },
    ]);
  } finally {
    setIsSending(false);
  }
}

async function executeMessage(
  text: string,
  apiKeyForRequest: string | null
) {
  if (!active) return;

  const agentProvider = active.provider ?? "gemini";

  const history = messages.map((message) => ({
    role: message.role,
    content: message.text,
  }));

  setMessages((previous) => [
    ...previous,
    { role: "user", text },
  ]);

  setChatInput("");

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
      provider: agentProvider,
      api_key: apiKeyForRequest,
    }),
  });

  const responseText = await response.text();

let data;

try {
  data = JSON.parse(responseText);
} catch {
  console.error("Resposta não JSON:", responseText);
  throw new Error(
    `O servidor retornou uma resposta inválida (HTTP ${response.status}). Verifique o console.`
  );
}

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
    { role: "assistant", text: resposta },
  ]);
}

async function unlockAndSendMessage() {
  if (!active || !pendingMessage || isSending) return;

  if (!unlockPassword) {
    setUnlockError("Informe sua senha.");
    return;
  }

  setIsSending(true);
  setUnlockError("");

  try {
    const credential = await unlockCredential(
      active.id,
      unlockPassword
    );
    setUnlockedCredentials((previous) => ({
      ...previous,
      [active.id]: {
        provider: credential.provider,
        apiKey: credential.apiKey,
      },
    }));
    setLastActivityByAgent((previous) => ({
      ...previous,
      [active.id]: Date.now(),
    }));
    setSessionNotice("");

    if (credential.provider !== active.provider) {
      throw new Error(
        "O provedor da credencial não corresponde ao agente."
      );
    }

    const text = pendingMessage;

    setShowUnlockModal(false);
    setUnlockPassword("");
    setPendingMessage("");

    await executeMessage(text, credential.apiKey);
  } catch (error) {
    setUnlockError(
      error instanceof Error
        ? error.message
        : "Não foi possível desbloquear a credencial."
    );
  } finally {
    setIsSending(false);
  }
}
  function lockCredentials() {
    if (!active) return;

    setUnlockedCredentials((previous) => {
      const updated = { ...previous };
      delete updated[active.id];
      return updated;
    });

    setLastActivityByAgent((previous) => {
      const updated = { ...previous };
      delete updated[active.id];
      return updated;
    });

    setShowUnlockModal(false);
    setUnlockPassword("");
    setPendingMessage("");
    setUnlockError("");

    setSessionNotice(
      `Credencial de ${active.name} bloqueada. Informe a senha novamente para continuar.`
    );
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

                {agents.map((agent) => {
                  const lastActivity =
                    lastActivityByAgent[agent.id] ?? clockNow;

                  const remainingTime = Math.max(
                    0,
                    IDLE_TIMEOUT_MS - (clockNow - lastActivity)
                  );

                  const minutes = Math.floor(remainingTime / 60000);
                  const seconds = Math.floor((remainingTime % 60000) / 1000);

                  const formattedTime = `${String(minutes).padStart(2, "0")}:${String(
                    seconds
                  ).padStart(2, "0")}`;

                  return (
                    <article className="agent-card" key={agent.id}>
                      <div className="agent-avatar">
                        <Bot size={26} />
                      </div>

                      <h3>{agent.name}</h3>

                      <p>{agent.purpose}</p>

                      <div
                        className={`credential-status ${
                          credentialStatus[agent.id] ?? "loading"
                        }`}
                      >
                        {credentialStatus[agent.id] === "unlocked" && (
                          <>
                            <Check size={14} />
                            Desbloqueada
                          </>
                        )}

                        {credentialStatus[agent.id] === "locked" && (
                          <>
                            <LockKeyhole size={14} />
                            Bloqueada
                          </>
                        )}

                        {credentialStatus[agent.id] === "missing" && (
                          <>
                            <LockKeyhole size={14} />
                            Sem credencial
                          </>
                        )}

                        {credentialStatus[agent.id] === "local" && (
                          <>
                            <Laptop size={14} />
                            Modelo local
                          </>
                        )}

                        {!credentialStatus[agent.id] && "Verificando credencial..."}
                      </div>

                      {credentialStatus[agent.id] === "unlocked" && (
                        <div className="credential-timer">
                          <LockKeyhole size={13} />
                          Bloqueio automático em {formattedTime}
                        </div>
                      )}

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
                          className="secondary"
                          onClick={() => {
                            setSelected(agent.id);
                            setDocuments([]);
                            carregarDocumentos(agent.id);
                            setScreen("documents");
                          }}
                        >
                          <Files size={16} />
                          Documentos
                        </button>

                        <button
                          className="icon-button"
                          aria-label={`Excluir ${agent.name}`}
                          onClick={() => {
                            if (confirm(`Excluir ${agent.name}?`)) {
                              setAgents((previous) =>
                                previous.filter((item) => item.id !== agent.id)
                              );

                              if (selected === agent.id) {
                                setSelected(null);
                                setMessages([]);
                                setScreen("home");
                              }

                              setUnlockedCredentials((previous) => {
                                const updated = { ...previous };
                                delete updated[agent.id];
                                return updated;
                              });

                              setLastActivityByAgent((previous) => {
                                const updated = { ...previous };
                                delete updated[agent.id];
                                return updated;
                              });
                            }
                          }}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </article>
                  );
                })}

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
              <div className="form-group">
                <label htmlFor="knowledgeBaseType">Base de conhecimento</label>

                <select
                  id="knowledgeBaseType"
                  value={draft.knowledgeBaseType}
                  onChange={(e) =>
                    setDraft((current) => ({
                      ...current,
                      knowledgeBaseType: e.target.value as "test" | "custom",
                    }))
                  }
                >
                  <option value="test">Base compartilhada de teste</option>
                  <option value="custom">Base própria do agente</option>
                </select>
              </div>

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
                    <label
                      htmlFor="credential-password"
                      style={{ marginTop: "18px" }}
                    >
                      Senha para proteger a chave de API
                    </label>

                    <input
                      id="credential-password"
                      type="password"
                      value={credentialPassword}
                      onChange={(e) =>
                        setCredentialPassword(e.target.value)
                      }
                      placeholder="Crie uma senha com pelo menos 12 caracteres"
                      autoComplete="new-password"
                      minLength={12}
                    />
                  </>
                )}

                <p className="lead">
                  {provider === "llama"
                    ? "O agente utilizará o modelo Llama configurado no backend. Nenhuma chave de API é necessária."
                    : "Sua chave de API será criptografada localmente e protegida pela senha definida acima. A senha não será armazenada. Se esquecê-la, será necessário cadastrar uma nova credencial."}
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
              {showUnlockModal && (
                <div className="credential-overlay">
                  <div
                    className="credential-modal"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="unlock-title"
                  >
                    <div className="guide-bot">
                      <Bot size={30} />
                    </div>

                    <h2 id="unlock-title">
                      Desbloquear credencial
                    </h2>

                    <p className="lead">
                      Digite a senha que você definiu ao cadastrar
                      a chave de API de {active.name}.
                    </p>

                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        unlockAndSendMessage();
                      }}
                    >
                      <label htmlFor="unlock-password">
                        Senha de acesso
                      </label>

                      <input
                        id="unlock-password"
                        type="password"
                        value={unlockPassword}
                        onChange={(e) => setUnlockPassword(e.target.value)}
                        placeholder="Digite sua senha"
                        autoComplete="current-password"
                        autoFocus
                        disabled={isSending}
                      />

                      {unlockError && (
                        <p className="credential-error">
                          {unlockError}
                        </p>
                      )}

                      <button
                        className="primary full"
                        type="submit"
                        disabled={!unlockPassword || isSending}
                      >
                        {isSending ? "Desbloqueando..." : "Desbloquear e enviar"}
                      </button>

                      <button
                        className="secondary full"
                        type="button"
                        disabled={isSending}
                        onClick={() => {
                          setShowUnlockModal(false);
                          setUnlockPassword("");
                          setUnlockError("");
                          setPendingMessage("");
                        }}
                      >
                        Cancelar
                      </button>
                    </form>
                  </div>
                </div>
              )}

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
                  {sessionNotice && (
                    <div className="notice">
                      {sessionNotice}
                    </div>
                  )}
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
                      {providerNames[active.provider ?? "gemini"]}.
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

          {screen === "documents" && active && (
            <section className="workspace">
              <div className="section-heading">
                <button
                  className="secondary"
                  onClick={() => setScreen("home")}
                >
                  <ArrowLeft size={16} />
                  Voltar
                </button>

                <h2>Documentos — {active.name}</h2>
                <p>Gerencie os documentos da base de conhecimento deste agente.</p>
              </div>

              <div className="form-card">
                <label htmlFor="document-upload">
                  Adicionar documentos (PDF, CSV, XLSX ou JSON)
                </label>

                <input
                  id="document-upload"
                  type="file"
                  accept=".pdf,.csv,.xlsx,.json"
                  multiple
                  disabled={isUploadingDocuments}
                  onChange={(e) => {
                    enviarDocumentos(e.target.files);
                    e.target.value = "";
                  }}
                />

                {isUploadingDocuments && (
                  <p className="success">{documentSuccess}</p>
                )}
              </div>

              {isLoadingDocuments ? (
                <p>Carregando documentos...</p>
              ) : documentError ? (
                <p className="error">{documentError}</p>
              ) : documents.length === 0 ? (
                <p>Nenhum documento cadastrado.</p>
              ) : (
                <div className="document-list">
                  {documents.map((document) => (
                    <div className="document-item" key={document.id}>
                      <div>
                        <strong>{document.nome}</strong>
                        <p>
                          {formatarTamanho(document.tamanho)} · Status: {document.status}
                        </p>
                        <p>
                          Enviado em: {formatarData(document.data_criacao)}
                        </p>
                        </div>
                        <button
                          className="secondary"
                          onClick={() => indexarDocumento(document.id)}
                          disabled={
                            indexingDocumentId !== null ||
                            document.status === "processing"
                          }
                        >
                          {indexingDocumentId === document.id
                            ? "Indexando..."
                            : document.status === "indexed"
                            ? "Reindexar"
                            : "Indexar"}
                        </button>
                      <button
                        className="icon-button"
                        title="Excluir documento"
                        aria-label={`Excluir ${document.nome}`}
                        onClick={async () => {
                          const confirmed = confirm(
                            `Deseja excluir o documento ${document.nome}?`
                          );

                          if (!confirmed) return;

                          setDocumentError("");
                          setDocumentSuccess("");


                          try {
                            const response = await fetch(
                              `/api/agents/${active.id}/documents?documentId=${document.id}`,
                              { method: "DELETE" }
                            );

                            const data = await response.json();

                            if (!response.ok) {
                              throw new Error(
                                data.detail || "Erro ao excluir documento."
                              );
                            }
                            setDocumentSuccess("Documento excluído com sucesso!");
                            await carregarDocumentos(active.id);

                          } catch (error) {
                            setDocumentError(
                              error instanceof Error
                                ? error.message
                                : "Não foi possível excluir o documento."
                            );
                          }
                        }}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          <button
            className="secondary"
            onClick={lockCredentials}
            disabled={!active || !unlockedCredentials[active.id]}
            title="Bloquear todas as credenciais desta sessão"
          >
            <LockKeyhole size={16} />
            Bloquear
          </button>

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
