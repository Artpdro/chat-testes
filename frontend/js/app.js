/**
 * FinBot Business — app.js
 * Sistema multi-módulo com sidebar, painel dinâmico e card preview.
 */

/* ════════════════════════════════════════════════════════
   CONFIGURAÇÃO DOS MÓDULOS
════════════════════════════════════════════════════════ */
const MODULES = {
  geral: {
    icon: '◈', label: 'Início', desc: 'Todos os módulos',
    color: '#6366f1', colorDim: 'rgba(99,102,241,.1)', colorGlow: 'rgba(99,102,241,.22)',
    chips: ['O que você consegue fazer?', 'Diagnóstico rápido', 'Pesquisa de mercado', 'Reforma tributária no meu negócio'],
    panelTabs: [{ id: 'fontes', label: 'Fontes' }, { id: 'detalhes', label: 'Detalhes' }],
  },
  diagnostico: {
    icon: '🔬', label: 'Diagnóstico', desc: 'Análise da empresa',
    color: '#6366f1', colorDim: 'rgba(99,102,241,.1)', colorGlow: 'rgba(99,102,241,.22)',
    chips: ['Diagnóstico do meu negócio', 'Pontos críticos para melhorar', 'Como está minha saúde financeira?', 'O que priorizar agora?'],
    panelTabs: [
      { id: 'diagnostico', label: 'Diagnóstico' },
      { id: 'recomendacoes', label: 'Recomendações' },
      { id: 'plano', label: 'Plano de Ação' },
      { id: 'fontes', label: 'Fontes' },
    ],
  },
  mercado: {
    icon: '📊', label: 'Mercado', desc: 'Pesquisa de nicho',
    color: '#0ea5e9', colorDim: 'rgba(14,165,233,.1)', colorGlow: 'rgba(14,165,233,.22)',
    chips: ['Analise meu nicho de mercado', 'Oportunidades no meu setor', 'Tendências que afetam meu negócio', 'Como se destacar da concorrência?'],
    panelTabs: [
      { id: 'nicho', label: 'Resumo do Nicho' },
      { id: 'oportunidades', label: 'Oportunidades' },
      { id: 'riscos', label: 'Riscos' },
      { id: 'fontes', label: 'Fontes' },
    ],
  },
  tributario: {
    icon: '⚖️', label: 'Reforma Tributária', desc: 'Novo modelo fiscal',
    color: '#f59e0b', colorDim: 'rgba(245,158,11,.1)', colorGlow: 'rgba(245,158,11,.22)',
    chips: ['Como a reforma me afeta?', 'O que é CBS e IBS?', 'Cronograma da transição fiscal', 'O que preciso fazer agora?'],
    panelTabs: [
      { id: 'impacto', label: 'Impacto' },
      { id: 'acoes', label: 'Ações' },
      { id: 'cronograma', label: 'Cronograma' },
    ],
  },
  nr1: {
    icon: '🛡️', label: 'NR-1', desc: 'Compliance e PGR',
    color: '#10b981', colorDim: 'rgba(16,185,129,.1)', colorGlow: 'rgba(16,185,129,.22)',
    chips: ['O que mudou na NR-1?', 'Como implementar o PGR?', 'Quais são as penalidades?', 'Checklist de conformidade'],
    panelTabs: [
      { id: 'conformidade', label: 'Conformidade' },
      { id: 'acoes', label: 'Ações' },
      { id: 'checklist', label: 'Checklist' },
    ],
  },
  cards: {
    icon: '🎨', label: 'Gerador de Cards', desc: 'Conteúdo para redes',
    color: '#ec4899', colorDim: 'rgba(236,72,153,.1)', colorGlow: 'rgba(236,72,153,.22)',
    chips: ['Card sobre a SELIC hoje', 'Post sobre reforma tributária', 'Dica financeira para empresas', 'Card sobre oportunidades de mercado'],
    panelTabs: [{ id: 'preview', label: 'Preview do Card' }, { id: 'detalhes', label: 'Detalhes' }],
  },
  assistentes: {
    icon: '🤖', label: 'Assistentes', desc: 'Especialistas por área',
    color: '#8b5cf6', colorDim: 'rgba(139,92,246,.1)', colorGlow: 'rgba(139,92,246,.22)',
    chips: ['Assistente jurídico', 'Consultor financeiro', 'Especialista em RH', 'Consultor de marketing'],
    panelTabs: [{ id: 'fontes', label: 'Fontes' }, { id: 'detalhes', label: 'Detalhes' }],
  },
};

// Mapeamento de seções da resposta → tab do painel
const SECTION_TAB_MAP = {
  diagnostico: { 'Diagnóstico': 'diagnostico', 'Recomendações': 'recomendacoes', 'Próximo Passo': 'plano' },
  mercado:     { 'Resumo do Nicho': 'nicho', 'Oportunidades': 'oportunidades', 'Riscos': 'riscos', 'Leitura Estratégica': 'nicho' },
  tributario:  { 'Impacto no Negócio': 'impacto', 'Ações Necessárias': 'acoes', 'Cronograma': 'cronograma' },
  nr1:         { 'Status de Conformidade': 'conformidade', 'Ações Imediatas': 'acoes', 'Checklist Básico': 'checklist' },
};

/* ════════════════════════════════════════════════════════
   ESTADO
════════════════════════════════════════════════════════ */
const state = {
  modulo:    'geral',
  carregando: false,
  historicos: {},      // { [modulo]: MensagemChat[] }
  ultimaResposta: null,
  activeTab:  null,
};

function getHistorico() {
  return state.historicos[state.modulo] ?? [];
}
function pushHistorico(role, content) {
  if (!state.historicos[state.modulo]) state.historicos[state.modulo] = [];
  state.historicos[state.modulo].push({ role, content });
  // Mantém últimas 20 trocas
  if (state.historicos[state.modulo].length > 20) {
    state.historicos[state.modulo] = state.historicos[state.modulo].slice(-20);
  }
}

/* ════════════════════════════════════════════════════════
   API
════════════════════════════════════════════════════════ */
const API = window.location.hostname.match(/^(localhost|127\.0\.0\.1)$/)
  ? 'http://localhost:8000/api'
  : '/api';

/* ════════════════════════════════════════════════════════
   DOM
════════════════════════════════════════════════════════ */
const sidebar      = document.getElementById('sidebar');
const sidebarToggle= document.getElementById('sidebar-toggle');
const mobileToggle = document.getElementById('mobile-toggle');
const modNav       = document.getElementById('mod-nav');
const topCrumbIcon = document.getElementById('crumb-icon');
const topCrumbLabel= document.getElementById('crumb-label');
const welcome      = document.getElementById('welcome');
const messages     = document.getElementById('messages');
const chatScroll   = document.getElementById('chat-scroll');
const chipsRow     = document.getElementById('chips-row');
const userInput    = document.getElementById('user-input');
const sendBtn      = document.getElementById('send-btn');
const infoPanel    = document.getElementById('info-panel');
const panelTabs    = document.getElementById('panel-tabs');
const panelBody    = document.getElementById('panel-body');
const panelMeta    = document.getElementById('panel-meta');
const panelToggle  = document.getElementById('panel-toggle');

/* ════════════════════════════════════════════════════════
   MARKED.JS CONFIG
════════════════════════════════════════════════════════ */
if (window.marked) {
  marked.setOptions({ breaks: true, gfm: true });
}
function md(text) {
  if (!text) return '';
  return window.marked ? marked.parse(text) : text.replace(/\n/g, '<br>');
}

/* ════════════════════════════════════════════════════════
   SIDEBAR
════════════════════════════════════════════════════════ */
function renderSidebar() {
  modNav.innerHTML = '';
  Object.entries(MODULES).forEach(([key, mod]) => {
    const btn = document.createElement('button');
    btn.className = 'mod-btn' + (key === state.modulo ? ' active' : '');
    btn.dataset.module = key;
    btn.innerHTML = `
      <span class="mod-icon">${mod.icon}</span>
      <span class="mod-info">
        <span class="mod-label">${mod.label}</span>
        <span class="mod-desc">${mod.desc}</span>
      </span>
      <span class="mod-dot"></span>`;
    btn.addEventListener('click', () => setModule(key));
    modNav.appendChild(btn);
  });
}

sidebarToggle.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
});
mobileToggle.addEventListener('click', () => {
  sidebar.classList.toggle('mobile-open');
});
document.addEventListener('click', e => {
  if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
    sidebar.classList.remove('mobile-open');
  }
});

/* ════════════════════════════════════════════════════════
   MÓDULO SWITCH
════════════════════════════════════════════════════════ */
function setModule(key) {
  if (!(key in MODULES)) return;
  state.modulo = key;
  const mod = MODULES[key];

  // Atualiza tema (CSS vars)
  const root = document.documentElement.style;
  root.setProperty('--accent', mod.color);
  root.setProperty('--accent-dim', mod.colorDim);
  root.setProperty('--accent-glow', mod.colorGlow);

  // Atualiza breadcrumb
  topCrumbIcon.textContent = mod.icon;
  topCrumbLabel.textContent = mod.label;

  // Atualiza sidebar
  document.querySelectorAll('.mod-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.module === key);
  });

  // Renderiza welcome do módulo
  renderWelcome(key);

  // Limpa chat ao trocar de módulo
  messages.innerHTML = '';

  // Atualiza chips
  renderChips(mod.chips);

  // Reseta painel
  panelTabs.innerHTML = '';
  panelBody.innerHTML = '<div class="pane-empty">Faça uma pergunta para ver os resultados aqui.</div>';
  panelMeta.textContent = '';
  infoPanel.classList.add('collapsed');

  sidebar.classList.remove('mobile-open');
  userInput.focus();
}

/* ════════════════════════════════════════════════════════
   WELCOME SCREEN
════════════════════════════════════════════════════════ */
function renderWelcome(key) {
  const mod = MODULES[key];

  if (key === 'geral') {
    const cards = Object.entries(MODULES)
      .filter(([k]) => k !== 'geral')
      .map(([k, m]) => `
        <div class="mod-card" data-module="${k}">
          <span class="mc-icon">${m.icon}</span>
          <div class="mc-label">${m.label}</div>
          <div class="mc-desc">${m.desc}</div>
        </div>`)
      .join('');

    welcome.innerHTML = `
      <div class="welcome-hero">
        <span class="w-icon">◈</span>
        <h1>I.A provisoria de testes</h1>
        <p>Diagnósticos, pesquisas de mercado, conformidade e conteúdo — tudo em um lugar.</p>
      </div>
      <div class="mod-grid">${cards}</div>`;

    welcome.querySelectorAll('.mod-card').forEach(card => {
      card.addEventListener('click', () => setModule(card.dataset.module));
    });

  } else {
    const exampleChips = mod.chips.slice(0, 3)
      .map(q => `<button class="chip" data-q="${q}">${q}</button>`)
      .join('');

    welcome.innerHTML = `
      <div class="welcome-mod">
        <span class="w-icon">${mod.icon}</span>
        <h2>${mod.label}</h2>
        <p>${mod.desc}</p>
        <div class="welcome-chips">${exampleChips}</div>
      </div>`;

    welcome.querySelectorAll('.chip').forEach(btn => {
      btn.addEventListener('click', () => {
        if (state.carregando) return;
        userInput.value = btn.dataset.q;
        adjustHeight();
        enviar();
      });
    });
  }
}

/* ════════════════════════════════════════════════════════
   CHIPS
════════════════════════════════════════════════════════ */
function renderChips(lista) {
  chipsRow.innerHTML = '';
  lista.forEach(texto => {
    const btn = document.createElement('button');
    btn.className = 'chip';
    btn.textContent = texto;
    btn.addEventListener('click', () => {
      if (state.carregando) return;
      userInput.value = texto;
      adjustHeight();
      enviar();
    });
    chipsRow.appendChild(btn);
  });
}

/* ════════════════════════════════════════════════════════
   MESSAGES
════════════════════════════════════════════════════════ */
function addUserMsg(texto) {
  const div = document.createElement('div');
  div.className = 'msg-user';
  div.innerHTML = `
    <div class="bubble">${md(texto)}</div>
    <div class="msg-meta"><span class="msg-time">${hora()}</span></div>`;
  messages.appendChild(div);
  scrollBottom();
}

function addBotMsg(data) {
  const { resposta, nivel_confianca, observacoes } = data;
  const confLabel = { alto: 'Alta confiança', medio: 'Confiança parcial', baixo: 'Dados limitados', indisponivel: 'Sem dados' };
  const obs = observacoes ? `<div class="obs-box">${observacoes}</div>` : '';
  const div = document.createElement('div');
  div.className = 'msg-bot';
  div.innerHTML = `
    <div class="bubble">${md(resposta)}</div>
    ${obs}
    <div class="msg-meta">
      <span class="conf conf-${nivel_confianca}">${confLabel[nivel_confianca] ?? nivel_confianca}</span>
      <span class="msg-time">${hora()}</span>
    </div>`;
  messages.appendChild(div);
  scrollBottom();
}

function addLoading() {
  const div = document.createElement('div');
  div.className = 'msg-bot loading';
  div.id = 'loading-msg';
  div.innerHTML = `
    <div class="bubble">
      <div class="dots"><span></span><span></span><span></span></div>
      <span class="loading-label">Processando…</span>
    </div>`;
  messages.appendChild(div);
  scrollBottom();
  return div;
}

function scrollBottom() { chatScroll.scrollTop = chatScroll.scrollHeight; }
function hora() { return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }); }

/* ════════════════════════════════════════════════════════
   PAINEL INFERIOR
════════════════════════════════════════════════════════ */

// Renderiza as tabs do painel conforme o módulo ativo
function renderPanelTabs(tabsDef, activeId) {
  panelTabs.innerHTML = '';
  state.activeTab = activeId ?? tabsDef[0]?.id;
  tabsDef.forEach(tab => {
    const btn = document.createElement('button');
    btn.className = 'ptab' + (tab.id === state.activeTab ? ' active' : '');
    btn.dataset.tab = tab.id;
    btn.textContent = tab.label;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ptab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeTab = tab.id;
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      const pane = document.getElementById(`pane-${tab.id}`);
      if (pane) pane.classList.add('active');
    });
    panelTabs.appendChild(btn);
  });
}

// Preenche o painel de acordo com o módulo e dados da resposta
function atualizarPainel(data) {
  const { fontes, nivel_confianca, observacoes, data_coleta, card_data, resposta } = data;
  const mod = MODULES[state.modulo];

  // Monta estrutura de panes
  panelBody.innerHTML = mod.panelTabs
    .map(t => `<div class="tab-pane ${t.id === mod.panelTabs[0].id ? 'active' : ''}" id="pane-${t.id}"></div>`)
    .join('');

  // Renderiza tab de fontes (se existir)
  const pFontes = document.getElementById('pane-fontes');
  if (pFontes) {
    pFontes.innerHTML = fontes?.length
      ? `<div class="sources-row">${fontes.map(f => `
          <div class="src-card ${f.dados_disponiveis ? 'ok' : 'err'}">
            <div class="src-name">${f.nome}</div>
            <div class="src-date">${f.data_consulta ?? data_coleta ?? '–'}</div>
            <span class="src-status ${f.dados_disponiveis ? 'ok' : 'err'}">
              ${f.dados_disponiveis ? 'DISPONÍVEL' : 'INDISPONÍVEL'}
            </span>
            ${f.url ? `<a class="src-link" href="${f.url}" target="_blank" rel="noopener">Ver fonte ↗</a>` : ''}
          </div>`).join('')}</div>`
      : '<div class="pane-empty">Nenhuma fonte externa consultada neste módulo.</div>';
  }

  // Renderiza tab de detalhes (se existir)
  const pDetalhes = document.getElementById('pane-detalhes');
  if (pDetalhes) {
    const confLabels = { alto: 'Alta', medio: 'Parcial', baixo: 'Baixa', indisponivel: '–' };
    pDetalhes.innerHTML = `
      <div class="details-row">
        <div class="detail-card">
          <div class="dc-label">Confiança</div>
          <div class="dc-value"><span class="conf conf-${nivel_confianca}">${confLabels[nivel_confianca]}</span></div>
        </div>
        <div class="detail-card">
          <div class="dc-label">Coleta</div>
          <div class="dc-value" style="font-size:11.5px">${data_coleta ?? '–'}</div>
        </div>
        ${observacoes ? `<div class="detail-card" style="min-width:100%;max-width:100%">
          <div class="dc-label">Observações</div><div class="dc-obs">${observacoes}</div>
        </div>` : ''}
        <div class="detail-card" style="min-width:100%;max-width:100%">
          <div class="dc-label">Aviso</div>
          <div class="dc-obs" style="color:var(--t2)">Informação educativa. Não constitui assessoria profissional.</div>
        </div>
      </div>`;
  }

  // Módulo CARDS — preview visual
  if (state.modulo === 'cards' && card_data) {
    const pPreview = document.getElementById('pane-preview');
    if (pPreview) renderCardPreview(pPreview, card_data);
  }

  // Módulos com seções estruturadas
  if (SECTION_TAB_MAP[state.modulo] && resposta) {
    extrairSecoes(resposta, SECTION_TAB_MAP[state.modulo]);
  }

  // Tabs + status
  renderPanelTabs(mod.panelTabs);
  const ok = fontes?.filter(f => f.dados_disponiveis).length ?? 0;
  const total = fontes?.length ?? 0;
  panelMeta.textContent = total ? `${ok}/${total} fontes ok` : '';

  infoPanel.classList.remove('collapsed');
}

// Extrai seções (## Título) e distribui nas tabs corretas
function extrairSecoes(texto, mapa) {
  const partes = texto.split(/^##\s+/m);
  if (partes.length < 2) return;

  partes.slice(1).forEach(parte => {
    const nl = parte.indexOf('\n');
    const titulo = (nl > 0 ? parte.slice(0, nl) : parte).trim();
    const conteudo = nl > 0 ? parte.slice(nl).trim() : '';

    // Procura qual tab recebe este bloco
    for (const [header, tabId] of Object.entries(mapa)) {
      if (titulo.toLowerCase().includes(header.toLowerCase())) {
        const pane = document.getElementById(`pane-${tabId}`);
        if (pane) {
          const bloco = document.createElement('div');
          bloco.className = 'section-block';
          bloco.innerHTML = `
            <h4>${titulo}</h4>
            <div class="content">${md(conteudo)}</div>`;
          pane.innerHTML = '';
          pane.appendChild(bloco);
        }
        break;
      }
    }
  });
}

// Renderiza card visual no painel
function renderCardPreview(pane, card) {
  pane.innerHTML = `
    <div class="card-preview-wrap">
      <div class="card-preview">
        <div class="cp-title">${esc(card.titulo ?? '')}</div>
        ${card.subtitulo ? `<div class="cp-subtitle">${esc(card.subtitulo)}</div>` : ''}
        <div class="cp-body">${esc(card.corpo ?? '')}</div>
        <div class="cp-cta">${esc(card.cta ?? '')}</div>
        <div class="cp-hashtags">${(card.hashtags ?? []).join(' ')}</div>
      </div>
      <div class="card-meta">
        <h4>Conteúdo do Card</h4>
        <div class="card-field"><div class="cf-label">Título</div><div class="cf-value">${esc(card.titulo ?? '')}</div></div>
        ${card.subtitulo ? `<div class="card-field"><div class="cf-label">Subtítulo</div><div class="cf-value">${esc(card.subtitulo)}</div></div>` : ''}
        <div class="card-field"><div class="cf-label">Corpo</div><div class="cf-value">${esc(card.corpo ?? '')}</div></div>
        <div class="card-field"><div class="cf-label">CTA</div><div class="cf-value">${esc(card.cta ?? '')}</div></div>
        <div class="card-field"><div class="cf-label">Hashtags</div><div class="cf-value">${(card.hashtags ?? []).join('  ')}</div></div>
      </div>
    </div>`;
}

function esc(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Toggle painel
panelToggle.addEventListener('click', () => infoPanel.classList.toggle('collapsed'));

/* ════════════════════════════════════════════════════════
   ENVIO
════════════════════════════════════════════════════════ */
async function enviar() {
  const texto = userInput.value.trim();
  if (!texto || state.carregando) return;

  // Remove welcome na primeira mensagem
  if (welcome.innerHTML) welcome.innerHTML = '';

  chipsRow.innerHTML = '';
  state.carregando = true;
  sendBtn.disabled = true;
  userInput.value = '';
  userInput.style.height = '22px';

  addUserMsg(texto);
  const loadEl = addLoading();

  try {
    const res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensagem: texto,
        historico: getHistorico().slice(-10),
        modulo: state.modulo,
      }),
    });

    loadEl.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? `Erro HTTP ${res.status}`);
    }

    const data = await res.json();

    pushHistorico('user', texto);
    pushHistorico('assistant', data.resposta);
    state.ultimaResposta = data;

    addBotMsg(data);
    atualizarPainel(data);
    renderChips(MODULES[state.modulo].chips);

  } catch (err) {
    loadEl.remove();
    const div = document.createElement('div');
    div.className = 'msg-bot';
    div.innerHTML = `
      <div class="bubble">
        <p><strong style="color:var(--red)">Não foi possível processar.</strong></p>
        <p style="color:var(--t2);font-size:13px;margin-top:5px">${esc(err.message)}</p>
        <p style="color:var(--t3);font-size:12px;margin-top:4px">
          Verifique se o backend está em execução e se <code>.env</code> está configurado.
        </p>
      </div>`;
    messages.appendChild(div);
    scrollBottom();
  } finally {
    state.carregando = false;
    sendBtn.disabled = false;
    userInput.focus();
    scrollBottom();
  }
}

/* ════════════════════════════════════════════════════════
   INPUT
════════════════════════════════════════════════════════ */
function adjustHeight() {
  userInput.style.height = '22px';
  userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
}
userInput.addEventListener('input', adjustHeight);
userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(); }
});
sendBtn.addEventListener('click', enviar);

/* ════════════════════════════════════════════════════════
   INIT
════════════════════════════════════════════════════════ */
renderSidebar();
setModule('geral');
