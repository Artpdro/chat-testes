# Chatbot Financeiro BR

Chatbot educativo e de inteligência de negócios para pequenas e médias empresas brasileiras. Integra o modelo GPT-4o da OpenAI com APIs públicas oficiais do governo brasileiro para fornecer análises em tempo real sobre economia, mercado, conformidade tributária e segurança do trabalho.

## Funcionalidades

- **7 módulos especializados** com prompts de sistema distintos
- **Function Calling da OpenAI** para busca automática de dados econômicos
- **Dados em tempo real** de fontes oficiais: BCB, IBGE, CVM e Portal da Transparência
- **Nível de confiança** calculado automaticamente conforme disponibilidade dos dados
- **Interface responsiva** em vanilla JS com suporte a Markdown

## Módulos

| Módulo | Descrição |
|---|---|
| **Início** | Visão geral e roteamento entre módulos |
| **Diagnóstico Empresarial** | Análise estruturada com dados de mercado (SELIC, IPCA, PIB, câmbio) |
| **Pesquisa de Mercado** | Oportunidades, riscos e estratégias com indicadores econômicos |
| **Reforma Tributária** | Impactos da EC 132/2023 (IBS, CBS, IS) por setor |
| **NR-1** | Conformidade com normas de saúde e segurança do trabalho (atualização 2024) |
| **Gerador de Cards** | Criação de conteúdo visual para redes sociais em formato JSON estruturado |
| **Assistentes Especializados** | Especialistas em jurídico, financeiro, RH, marketing, operações e tecnologia |

## Stack

- **Backend**: Python 3.12 + FastAPI + Uvicorn
- **IA**: OpenAI GPT-4o com Function Calling
- **HTTP assíncrono**: httpx + asyncio
- **Validação**: Pydantic v2
- **Frontend**: HTML5 + CSS3 + JavaScript (vanilla)

## Pré-requisitos

- Python 3.10+
- Chave de API da OpenAI (`sk-proj-...`)
- (Opcional) Chave do Portal da Transparência

## Instalação

```bash
# Clone o repositório
git clone https://github.com/Artpdro/chat-testes
cd financial-chatbot

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r backend/requirements.txt
```

## Configuração

Crie o arquivo `backend/.env`:

```env
# Obrigatório
OPENAI_API_KEY=

# Opcional — padrão: gpt-4o
OPENAI_MODEL=gpt-4o

TRANSPARENCIA_API_KEY=
```

As APIs do BCB, IBGE e CVM são públicas e não exigem autenticação.

## Execução

```bash
cd backend
uvicorn app:app --reload
```

Acesse `http://localhost:8000`.

Para produção:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Estrutura do Projeto

```
financial-chatbot/
├── backend/
│   ├── app.py                  # Entrypoint FastAPI, CORS, mount do frontend
│   ├── requirements.txt
│   ├── .env
│   ├── routers/
│   │   └── chat.py             # Endpoints /api/chat, /api/modulos, /api/fontes
│   ├── models/
│   │   └── schemas.py          # Schemas Pydantic (ChatRequest, ChatResponse, etc.)
│   └── services/
│       ├── openai_service.py   # Orquestração GPT-4o + function calling
│       ├── bcb_service.py      # Banco Central do Brasil – SGS
│       ├── ibge_service.py     # IBGE SIDRA
│       ├── cvm_service.py      # CVM Dados Abertos
│       └── transparencia_service.py  # Portal da Transparência
└── frontend/
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## API

### `POST /api/chat`

Envia uma mensagem para o módulo selecionado.

**Request**

```json
{
  "mensagem": "Como está a SELIC hoje?",
  "historico": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "modulo": "diagnostico"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `mensagem` | string (1–2000) | sim | Pergunta do usuário |
| `historico` | array | sim | Mensagens anteriores (máx. 20) |
| `modulo` | string | não | `geral` (padrão), `diagnostico`, `mercado`, `tributario`, `nr1`, `cards`, `assistentes` |

**Response**

```json
{
  "resposta": "A SELIC está em **13,75% a.a.**...",
  "fontes": [
    {
      "nome": "BCB/SGS",
      "url": "https://api.bcb.gov.br",
      "data_consulta": "2024-01-15 14:32",
      "dados_disponiveis": true,
      "descricao": "Taxa SELIC"
    }
  ],
  "data_coleta": "2024-01-15 14:32:10",
  "nivel_confianca": "alto",
  "observacoes": null,
  "dados_coletados": {},
  "card_data": null
}
```

| Campo | Descrição |
|---|---|
| `resposta` | Texto em Markdown com a resposta do assistente |
| `fontes` | Fontes consultadas e disponibilidade dos dados |
| `nivel_confianca` | `alto` (≥80% fontes OK) · `medio` (50–79%) · `baixo` (<50%) · `indisponivel` |
| `card_data` | Preenchido apenas no módulo `cards` (JSON com título, corpo, CTA, hashtags) |

### `GET /api/modulos`

Retorna a lista de módulos disponíveis.

### `GET /api/fontes`

Retorna as fontes de dados configuradas e seus requisitos de autenticação.

### `GET /health`

```json
{
  "status": "ok",
  "openai_configurado": true,
  "transparencia_configurado": false
}
```

## Fontes de Dados

| Fonte | Dados | Autenticação |
|---|---|---|
| [BCB/SGS](https://api.bcb.gov.br) | SELIC, CDI, IPCA, IGP-M, câmbio USD/EUR, PIB mensal, inadimplência | Não |
| [IBGE/SIDRA](https://servicodados.ibge.gov.br) | IPCA, PIB trimestral, desemprego (PNAD), INPC, população | Não |
| [CVM Dados Abertos](https://dados.cvm.gov.br) | Fundos de investimento, companhias abertas | Não |
| [Portal da Transparência](https://portaldatransparencia.gov.br) | Despesas federais, receitas, licitações por UF | Sim (gratuito) |

## Arquitetura

```
Usuário
  │
  ▼
Frontend (Vanilla JS)
  │  POST /api/chat
  ▼
FastAPI Router
  │
  ▼
OpenAI Service
  ├── Seleciona prompt de sistema por módulo
  ├── Chama GPT-4o com tools definidas
  │
  └── Function Calling (paralelo via asyncio.gather)
        ├── buscar_serie_bcb      → BCB/SGS
        ├── buscar_indicador_ibge → IBGE/SIDRA
        ├── buscar_dados_cvm      → CVM
        └── buscar_dados_transparencia → Portal da Transparência
```

**Módulos sem function calling** (raciocínio puro): `nr1`, `tributario`, `assistentes`

**Cálculo do nível de confiança**: após todas as chamadas, a proporção de fontes com dados disponíveis determina o nível exibido ao usuário.

## Desenvolvimento

```bash
# Rodar com hot-reload
uvicorn app:app --reload

# Acessar docs interativos da API
http://localhost:8000/docs

# Health check
curl http://localhost:8000/health
```
