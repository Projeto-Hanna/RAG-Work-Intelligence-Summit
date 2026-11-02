# AgentLab — protótipo v0.1

Web app responsivo para a oficina **Crie seu próprio agente de IA**, do Work Intelligence Summit.

## Requisitos
- Node.js 20.9+ (recomendado: Node 22)
- npm

## Rodar localmente

```bash
npm install
npm run dev
```

Abra http://localhost:3000 no navegador.

## Publicar na Vercel
1. Suba esta pasta para um repositório Git.
2. Importe o repositório na Vercel.
3. Use as configurações padrão de Next.js e faça o deploy.

## O que funciona
- Dashboard responsivo mobile-first.
- Criação guiada por perguntas (fluxo determinístico, sem IA).
- Configuração manual de agentes.
- Revisão/edição de instruções.
- Salvar e excluir agentes no localStorage do navegador.
- Chat demonstrativo com respostas simuladas.
- Exportar configuração em JSON.
- Tela demonstrativa de conexão com endpoint.

## O que NÃO está implementado
- Integração com LLM, backend ou execução real de agentes.
- Autenticação e persistência em servidor.
- Comunicação com endpoint local (a tela não faz requisições).
- Upload de documentos.
- Sincronização entre dispositivos.

**Atenção:** localStorage não sincroniza entre celular e computador e pode ser apagado. Exporte o JSON para preservar sua configuração.

## Próximas etapas
1. Definir contrato JSON e API do runtime.
2. Implementar backend e comunicação autenticada HTTPS.
3. Persistir agentes por usuário e importar configurações.
4. Adicionar upload de documentos e chat real.
5. Testar navegação mobile, acessibilidade e segurança.
