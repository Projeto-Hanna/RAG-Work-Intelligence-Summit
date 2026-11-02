 "use client";
import { useEffect, useState } from "react";
import { Bot, Plus, House, Sparkles, MessageCircle, Download, ArrowLeft, ArrowRight, Settings2, Trash2, Wifi, Laptop, Check, Send, Copy, Pencil, X } from "lucide-react";

type Agent = { id:string; name:string; purpose:string; tone:string; instructions:string; createdAt:string };
type Screen = "home"|"choose"|"guided"|"manual"|"review"|"chat"|"export"|"connection";
const purposes = ["Analisar documentos","Criar relatórios e KPIs","Produzir conteúdo","Organizar tarefas","Outra finalidade"];
const tones = ["Profissional e objetivo","Amigável e descontraído","Didático e detalhado"];
const initial:Agent = {id:"",name:"",purpose:"",tone:tones[0],instructions:"",createdAt:""};
const makeInstructions = (a:Agent) => `Você é um agente de IA chamado ${a.name || "Meu Agente"}.\nSua principal função é: ${a.purpose || "auxiliar o usuário em suas atividades"}.\nAdote um tom ${a.tone.toLowerCase()}.\nResponda de forma clara e útil. Quando não souber uma resposta, informe suas limitações. Não invente informações.`;
function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `agent-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}
export default function Home() {
 const [screen,setScreen]=useState<Screen>("home");
 const [agents,setAgents]=useState<Agent[]>([]);
 const [draft,setDraft]=useState<Agent>(initial);
 const [selected,setSelected]=useState<string|null>(null);
 const [step,setStep]=useState(0);
 const [answer,setAnswer]=useState("");
 const [messages,setMessages]=useState<{role:"user"|"assistant";text:string}[]>([]);
 const [chatInput,setChatInput]=useState("");
 const [endpoint,setEndpoint]=useState("");
 const [token,setToken]=useState("");
 const [connectionStatus,setConnectionStatus]=useState("");
 const [hydrated,setHydrated]=useState(false);
 useEffect(()=>{try {setAgents(JSON.parse(localStorage.getItem("agentlab-agents")||"[]"));}catch{} setHydrated(true)},[]);
 useEffect(()=>{if(hydrated)localStorage.setItem("agentlab-agents",JSON.stringify(agents))},[agents,hydrated]);
 const active=agents.find(a=>a.id===selected);
 function start(mode:"guided"|"manual"){setDraft({...initial});setStep(0);setAnswer("");setScreen(mode)}
 function nextGuided(){
  const value=answer.trim();
  if(!value)return;
  if(step===0)setDraft(d=>({...d,purpose:value}));
  if(step===1)setDraft(d=>({...d,name:value}));
  if(step===2)setDraft(d=>({...d,tone:value}));
  setAnswer(""); if(step===2)setScreen("review");else setStep(s=>s+1);
 }
 function saveAgent(){
  const a:Agent={...draft,id: draft.id || generateId(),createdAt:draft.createdAt||new Date().toISOString(),instructions:draft.instructions.trim()||makeInstructions(draft)};
  setAgents(prev=>[a,...prev.filter(item=>item.id!==a.id)]);setSelected(a.id);setScreen("chat");setMessages([]);
 }
 function exportAgent(){const a=active||draft;const blob=new Blob([JSON.stringify({schemaVersion:1,name:a.name,purpose:a.purpose,tone:a.tone,instructions:a.instructions},null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download=`${(a.name||"meu-agente").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g,"-")}.json`;link.click();URL.revokeObjectURL(url)}
 function sendMessage(){const text=chatInput.trim();if(!text)return;setMessages(prev=>[...prev,{role:"user",text},{role:"assistant",text:"Esta é uma resposta de demonstração. Seu agente já tem uma configuração exportável, mas a conexão com o modelo de IA ainda será implementada."}]);setChatInput("")}
 const prompts=["Qual tarefa você quer facilitar?","Qual nome você gostaria de dar ao agente?","Como ele deve se comunicar?"];
 const hints=["Ex.: Analisar relatórios e identificar tendências","Ex.: Analista Inteligente","Escolha abaixo ou descreva outro estilo"];
 return <div className="shell">
  <aside className="sidebar">
   <div className="brand"><div className="brand-icon"><Sparkles size={22}/></div><div><strong>AgentLab</strong><small>WORK INTELLIGENCE SUMMIT</small></div></div>
   <div className="nav">
    <button className={screen==="home"?"active":""} onClick={()=>setScreen("home")}><House size={19}/> Início</button>
    <button onClick={()=>setScreen("home")}><Bot size={19}/> Meus agentes <span className="nav-count">{agents.length}</span></button>
    <button className={["choose","guided","manual","review"].includes(screen)?"active":""} onClick={()=>setScreen("choose")}><Plus size={19}/> Criar agente</button>
    <button className={screen==="connection"?"active":""} onClick={()=>setScreen("connection")}><Wifi size={19}/> Ambiente</button>
   </div>
   <div className="sidebar-bottom"><span className="status-dot"/> Protótipo do workshop <small>v0.1 · Interface demonstrativa</small></div>
  </aside>
  <main className="main">
   <header className="topbar"><div className="mobile-brand"><Sparkles size={18}/> AgentLab</div><span className="event-label">WORK INTELLIGENCE SUMMIT</span><span className="pill"><span className="status-dot"/> Modo demonstração</span></header>
   <div className="content">
   {screen==="home"&&<><section className="hero"><div className="eyebrow"><Sparkles size={15}/> SEU LABORATÓRIO DE IA</div><h1>Suas ideias.<br/><span>Seu agente de IA.</span></h1><p>Crie, personalize e experimente agentes de inteligência artificial. Sem precisar escrever uma linha de código.</p><button className="primary" onClick={()=>setScreen("choose")}><Plus size={18}/> Criar meu agente <ArrowRight size={18}/></button><div className="hero-orb"><Bot size={72}/></div></section>
   <div className="section-heading"><div><h2>Meus agentes</h2><p>Continue de onde parou ou comece algo novo.</p></div><span className="counter">{agents.length} agente(s)</span></div>
   <div className="agent-grid">{agents.map(a=><article className="agent-card" key={a.id}><div className="agent-avatar"><Bot size={26}/></div><h3>{a.name}</h3><p>{a.purpose}</p><div className="card-actions"><button className="secondary" onClick={()=>{setSelected(a.id);setMessages([]);setScreen("chat")}}>Conversar <ArrowRight size={16}/></button><button className="icon-button" aria-label={`Excluir ${a.name}`} onClick={()=>{if(confirm(`Excluir ${a.name}?`))setAgents(v=>v.filter(x=>x.id!==a.id))}}><Trash2 size={17}/></button></div></article>)}<button className="new-card" onClick={()=>setScreen("choose")}><div className="plus-circle"><Plus size={23}/></div><strong>Novo agente</strong><span>Comece com uma ideia</span></button></div></>}
   {screen==="choose"&&<div className="narrow"><button className="back" onClick={()=>setScreen("home")}><ArrowLeft size={17}/> Voltar</button><div className="eyebrow">CRIAR AGENTE</div><h1>Como vamos começar?</h1><p className="lead">Escolha a maneira mais confortável de construir seu assistente.</p><div className="choice-grid"><button className="choice" onClick={()=>start("guided")}><div className="choice-icon"><MessageCircle/></div><span className="badge">RECOMENDADO</span><h3>Criação guiada</h3><p>Responda algumas perguntas e nós montamos as instruções do seu agente.</p><strong>Começar <ArrowRight size={16}/></strong></button><button className="choice" onClick={()=>start("manual")}><div className="choice-icon"><Settings2/></div><h3>Configuração manual</h3><p>Defina nome, objetivo, estilo e instruções diretamente.</p><strong>Configurar <ArrowRight size={16}/></strong></button></div></div>}
   {screen==="guided"&&<div className="narrow"><button className="back" onClick={()=>setScreen("choose")}><ArrowLeft size={17}/> Voltar</button><div className="step-row"><span>CRIANDO SEU AGENTE</span><span>Etapa {step+1} de 3</span></div><div className="progress"><span style={{width:`${(step+1)/3*100}%`}}/></div><div className="guide-bot"><Bot size={30}/></div><h1>{prompts[step]}</h1><p className="lead">{hints[step]}</p>{step===0&&<div className="suggestions">{purposes.map(p=><button key={p} onClick={()=>setAnswer(p)} className={answer===p?"selected":""}>{p}</button>)}</div>}{step===2&&<div className="suggestions">{tones.map(t=><button key={t} onClick={()=>setAnswer(t)} className={answer===t?"selected":""}>{t}</button>)}</div>}<label className="field-label" htmlFor="guided-answer">Sua resposta</label><input id="guided-answer" value={answer} onChange={e=>setAnswer(e.target.value)} onKeyDown={e=>e.key==="Enter"&&nextGuided()} placeholder="Digite sua resposta..."/><button className="primary full" disabled={!answer.trim()} onClick={nextGuided}>Continuar <ArrowRight size={17}/></button></div>}
   {screen==="manual"&&<div className="narrow"><button className="back" onClick={()=>setScreen("choose")}><ArrowLeft size={17}/> Voltar</button><div className="eyebrow">CONFIGURAÇÃO MANUAL</div><h1>Personalize seu agente</h1><p className="lead">Defina como seu agente deve agir e responder.</p><div className="form-card"><label>Nome do agente<input value={draft.name} onChange={e=>setDraft({...draft,name:e.target.value})} placeholder="Ex.: Analista Inteligente"/></label><label>Objetivo principal<input value={draft.purpose} onChange={e=>setDraft({...draft,purpose:e.target.value})} placeholder="Ex.: Analisar relatórios"/></label><label>Tom de voz<select value={draft.tone} onChange={e=>setDraft({...draft,tone:e.target.value})}>{tones.map(t=><option key={t}>{t}</option>)}</select></label><label>Instruções adicionais (opcional)<textarea rows={5} value={draft.instructions} onChange={e=>setDraft({...draft,instructions:e.target.value})} placeholder="Você é um agente que..."/></label></div><button className="primary full" disabled={!draft.name.trim()||!draft.purpose.trim()} onClick={()=>setScreen("review")}>Revisar agente <ArrowRight size={17}/></button></div>}
   {screen==="review"&&<div className="narrow"><button className="back" onClick={()=>setScreen("guided")}><ArrowLeft size={17}/> Voltar</button><div className="eyebrow">QUASE LÁ</div><h1>Seu agente está tomando forma ✨</h1><p className="lead">Confira as instruções antes de começar a conversar.</p><div className="review-card"><div className="review-head"><div className="agent-avatar"><Bot/></div><div><h3>{draft.name}</h3><p>{draft.purpose}</p></div></div><label>Instruções do agente<textarea rows={11} value={draft.instructions||makeInstructions(draft)} onChange={e=>setDraft({...draft,instructions:e.target.value})}/></label></div><button className="primary full" onClick={saveAgent}><Check size={18}/> Criar e testar agente</button></div>}
   {screen==="chat"&&active&&<div className="chat-layout"><div className="chat-header"><div className="agent-avatar small"><Bot size={21}/></div><div><h2>{active.name}</h2><p>{active.purpose}</p></div><button className="secondary" onClick={()=>{setDraft(active);setScreen("manual")}}><Pencil size={16}/> Editar</button><button className="secondary" onClick={()=>setScreen("export")}><Download size={16}/> Exportar</button></div><div className="messages">{messages.length===0?<div className="empty-chat"><div className="guide-bot"><Bot size={32}/></div><h2>Olá! Sou {active.name}.</h2><p>Seu agente está configurado. Faça uma pergunta para experimentar a interface.</p><div className="notice">O chat está em modo demonstrativo. Ainda não há um modelo de IA conectado.</div></div>:messages.map((m,i)=><div className={`message ${m.role}`} key={i}>{m.text}</div>)}</div><form className="chat-compose" onSubmit={e=>{e.preventDefault();sendMessage()}}><input aria-label="Mensagem" placeholder="Pergunte alguma coisa..." value={chatInput} onChange={e=>setChatInput(e.target.value)}/><button className="send" disabled={!chatInput.trim()} aria-label="Enviar"><Send size={19}/></button></form></div>}
   {screen==="export"&&active&&<div className="narrow"><button className="back" onClick={()=>setScreen("chat")}><ArrowLeft size={17}/> Voltar ao chat</button><div className="eyebrow">LEVE SEU AGENTE COM VOCÊ</div><h1>Seu agente, suas regras.</h1><p className="lead">Baixe as instruções e prepare-se para executar o agente no seu próprio ambiente.</p><div className="form-card"><div className="review-head"><div className="agent-avatar"><Download/></div><div><h3>{active.name}.json</h3><p>Configuração do agente · JSON</p></div></div><button className="primary full" onClick={exportAgent}><Download size={18}/> Baixar configuração</button></div><div className="notice">O arquivo exporta as instruções, não o modelo de IA. A estrutura de execução local será disponibilizada separadamente pela organização.</div><button className="secondary" onClick={()=>setScreen("connection")}><Laptop size={17}/> Configurar ambiente local</button></div>}
   {screen==="connection"&&<div className="narrow"><button className="back" onClick={()=>setScreen("home")}><ArrowLeft size={17}/> Voltar</button><div className="eyebrow">AMBIENTE DE EXECUÇÃO</div><h1>Conecte seu ambiente</h1><p className="lead">No futuro, você poderá usar um endpoint seguro para acessar seus agentes executados localmente.</p><div className="form-card"><label>Endpoint HTTPS<input type="url" value={endpoint} onChange={e=>setEndpoint(e.target.value)} placeholder="https://seu-endpoint.exemplo"/></label><label>Token de acesso<input type="password" value={token} onChange={e=>setToken(e.target.value)} placeholder="Token do ambiente"/></label><button className="primary full" onClick={()=>setConnectionStatus("Esta tela é apenas um protótipo. Nenhuma conexão foi realizada.")}>Testar conexão <Wifi size={17}/></button>{connectionStatus&&<div className="notice">{connectionStatus}</div>}</div><div className="notice">Não exponha APIs locais sem autenticação e HTTPS. Tokens digitados aqui não são armazenados nem enviados nesta versão.</div></div>}
   </div>
  </main>
  <nav className="mobile-nav"><button onClick={()=>setScreen("home")}><House size={20}/><span>Início</span></button><button onClick={()=>setScreen("home")}><Bot size={20}/><span>Agentes</span></button><button onClick={()=>setScreen("choose")}><Plus size={20}/><span>Criar</span></button><button onClick={()=>setScreen("connection")}><Wifi size={20}/><span>Ambiente</span></button></nav>
 </div>;
}
