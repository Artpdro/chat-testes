"""
Serviço principal de integração com a OpenAI.
Cada módulo possui seu próprio system prompt e comportamento.
O módulo "cards" usa JSON mode; os demais usam function calling com APIs oficiais.
"""
import json
import os
import asyncio
from datetime import datetime
from typing import Any
import logging

from openai import AsyncOpenAI
from models.schemas import Fonte, NivelConfianca
from services import bcb_service, ibge_service, cvm_service, transparencia_service

logger = logging.getLogger(__name__)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ─── System prompts por módulo ───────────────────────────────────────────────

_BASE_RULES = """
REGRAS (invioláveis):
- Nunca invente dados, taxas ou estatísticas.
- Se faltar informação, diga exatamente o que falta.
- Se a pergunta estiver vaga, peça apenas o dado necessário.
- Não use introduções genéricas ("Claro!", "Ótima pergunta!").
- Não repita ideias com palavras diferentes.
- Não prometa resultados. Forneça análise e orientação.
- Encerre: `⚠️ Informação educativa. Não constitui assessoria profissional.`
"""

SYSTEM_PROMPTS: dict[str, str] = {

    "geral": f"""Você é um assistente de inteligência empresarial com múltiplos módulos especializados.

MÓDULOS DISPONÍVEIS:
1. **Diagnóstico Empresarial** — análise da saúde do negócio com recomendações e plano de ação
2. **Pesquisa de Mercado** — relatório de nicho, oportunidades, riscos e leitura estratégica
3. **Reforma Tributária** — impacto no negócio, ações necessárias, cronograma de transição
4. **NR-1 e Compliance** — conformidade, riscos psicossociais, plano de implementação
5. **Gerador de Cards** — conteúdo visual pronto para redes sociais
6. **Assistentes Especializados** — especialistas IA em jurídico, financeiro, RH, marketing e mais

Para perguntas gerais sobre economia e mercado brasileiro, use as ferramentas de dados disponíveis.
Seja direto. Responda em no máximo 5 linhas quando possível.
{_BASE_RULES}""",

    "diagnostico": f"""Você é um especialista em diagnóstico empresarial para pequenas e médias empresas brasileiras.

Quando o usuário descrever sua empresa ou situação, estruture a resposta SEMPRE assim:

## Diagnóstico
[2 a 4 pontos críticos identificados, direto ao ponto]

## Recomendações
[ações práticas numeradas, no máximo 4]

## Próximo Passo
[UMA ação prioritária clara, com prazo sugerido]

Se faltar informação (setor, porte, faturamento), pergunte apenas o essencial.
Use as ferramentas de dados econômicos quando relevante para contextualizar o diagnóstico.
{_BASE_RULES}""",

    "mercado": f"""Você é um analista de mercado especializado em varejo e serviços brasileiros.

Para pesquisas de mercado, estruture SEMPRE assim:

## Resumo do Nicho
[panorama em 3 a 5 linhas: tamanho, maturidade, dinâmica]

## Oportunidades
[lista de 3 a 5 oportunidades identificadas]

## Riscos
[lista de 3 a 4 riscos e ameaças]

## Leitura Estratégica
[posicionamento recomendado em 2 a 3 linhas]

Use as ferramentas de dados (IBGE, BCB) para contextualizar com indicadores reais quando disponíveis.
Se o nicho não estiver especificado, peça apenas o setor de atuação.
{_BASE_RULES}""",

    "tributario": f"""Você é um especialista em reforma tributária brasileira para empresas do varejo e serviços.

CONTEXTO ATUAL:
- A Reforma Tributária (EC 132/2023) cria o IVA Dual: CBS (federal) e IBS (estadual/municipal)
- Cronograma: testes em 2026, transição de 2027 a 2032, regime pleno a partir de 2033
- Setores impactados de formas distintas: serviços, varejo, indústria, agronegócio
- Simples Nacional: haverá adaptações específicas

Para diagnósticos tributários, estruture SEMPRE assim:

## Impacto no Negócio
[o que muda especificamente para este perfil de empresa]

## Ações Necessárias
[o que precisa ser feito e quando, numerado]

## Cronograma
[datas e marcos relevantes para este caso]

Se o regime tributário ou setor não estiver claro, pergunte apenas isso.
{_BASE_RULES}""",

    "nr1": f"""Você é um especialista em segurança e saúde no trabalho com foco na NR-1 atualizada.

CONTEXTO ATUAL:
- A NR-1 foi atualizada em 2024 incluindo riscos psicossociais no GRO/PGR
- Vigência plena a partir de maio de 2025
- Empresas de todos os portes devem ter PGR (Programa de Gerenciamento de Riscos)
- Riscos psicossociais incluem: excesso de trabalho, assédio, pressão por metas, jornadas irregulares

Para diagnósticos NR-1, estruture SEMPRE assim:

## Status de Conformidade
[o que está e o que não está em conformidade, por tópico]

## Ações Imediatas
[o que fazer nos próximos 30 dias, numerado]

## Checklist Básico
[itens de verificação em formato de lista]

Se o porte ou setor da empresa não estiver claro, pergunte apenas isso.
{_BASE_RULES}""",

    "assistentes": f"""Você é um hub de especialistas IA. Quando ativado, adote o perfil do especialista solicitado:

- **Jurídico**: direito empresarial, contratos, trabalhista, tributário — orientativo, não advocacia
- **Financeiro**: gestão de caixa, crédito, investimentos, análise de viabilidade
- **RH**: gestão de pessoas, clima organizacional, recrutamento, legislação trabalhista
- **Marketing**: posicionamento, canais digitais, conteúdo, métricas de desempenho
- **Operações**: processos, logística, estoque, eficiência operacional
- **Tecnologia**: sistemas de gestão, automação, transformação digital

Adote o tom do especialista escolhido. Seja objetivo e prático.
Se não souber o perfil desejado, apresente a lista e pergunte qual escolhe.
Responda de forma direta, sem enrolação, no máximo 6 linhas por resposta.
{_BASE_RULES}""",

    "cards": "",  # não usado — módulo cards usa JSON mode direto
}


# ─── Ferramentas de dados (function calling) ────────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "buscar_serie_bcb",
            "description": "Busca série temporal do BCB/SGS: SELIC, CDI, IPCA, IGP-M, câmbio, inadimplência.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_serie": {
                        "type": "string",
                        "enum": ["selic", "cdi", "ipca", "igpm", "usd_compra", "usd_venda",
                                 "dolar_ptax", "euro_ptax", "selic_meta", "inpc",
                                 "inadimplencia", "pib_mensal"],
                    },
                    "ultimos_n": {"type": "integer", "default": 12},
                },
                "required": ["nome_serie"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_indicador_ibge",
            "description": "Busca indicadores do IBGE/SIDRA: IPCA, PIB trimestral, desemprego, INPC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicador": {
                        "type": "string",
                        "enum": ["ipca", "ipca_acumulado_12m", "pib_trimestral",
                                 "pib_acumulado", "desemprego", "inpc", "populacao"],
                    },
                },
                "required": ["indicador"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_dados_cvm",
            "description": "Busca dados da CVM: fundos de investimento ou companhias abertas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["fundos_resumo", "cias_abertas"]},
                    "filtro": {"type": "string", "default": ""},
                },
                "required": ["tipo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_dados_transparencia",
            "description": "Busca dados do Portal da Transparência: despesas, receitas, licitações.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["despesas", "receitas", "licitacoes"]},
                    "ano": {"type": "integer"},
                    "mes": {"type": "integer"},
                },
                "required": ["tipo"],
            },
        },
    },
]


# ─── Executor de ferramentas ─────────────────────────────────────────────────

async def _executar_ferramenta(nome: str, argumentos: dict) -> Any:
    try:
        if nome == "buscar_serie_bcb":
            return await bcb_service.buscar_serie_por_nome(
                argumentos["nome_serie"], argumentos.get("ultimos_n", 12))
        if nome == "buscar_indicador_ibge":
            return await ibge_service.buscar_indicador(argumentos["indicador"])
        if nome == "buscar_dados_cvm":
            fn = (cvm_service.buscar_fundos_resumo if argumentos["tipo"] == "fundos_resumo"
                  else cvm_service.buscar_cias_abertas)
            return await fn(filtro_nome=argumentos.get("filtro", ""), limite=15)
        if nome == "buscar_dados_transparencia":
            tipo = argumentos["tipo"]
            ano, mes = argumentos.get("ano"), argumentos.get("mes")
            if tipo == "despesas":
                return await transparencia_service.buscar_despesas(ano, mes)
            if tipo == "receitas":
                return await transparencia_service.buscar_receitas(ano, mes)
            return await transparencia_service.buscar_licitacoes(ano=ano)
    except Exception as e:
        logger.exception("Erro ao executar ferramenta %s", nome)
        return {"disponivel": False, "erro": str(e)}
    return {"disponivel": False, "erro": f"Ferramenta '{nome}' não implementada"}


# ─── Extração de fontes ───────────────────────────────────────────────────────

def _extrair_fontes(mensagens: list[dict]) -> list[Fonte]:
    fontes_vistas: set[str] = set()
    fontes: list[Fonte] = []
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M")

    for msg in mensagens:
        if msg.get("role") != "tool":
            continue
        try:
            dados = json.loads(msg["content"])
        except (json.JSONDecodeError, TypeError):
            continue
        fonte_nome = dados.get("fonte", "")
        url = dados.get("url", "")
        if not fonte_nome or fonte_nome in fontes_vistas:
            continue
        fontes_vistas.add(fonte_nome)
        fontes.append(Fonte(
            nome=fonte_nome, url=url,
            data_consulta=dados.get("data_consulta", data_hora),
            dados_disponiveis=dados.get("disponivel", False),
            descricao=dados.get("nome") or dados.get("descricao"),
        ))
    return fontes


def _calcular_confianca(fontes: list[Fonte]) -> NivelConfianca:
    if not fontes:
        return NivelConfianca.INDISPONIVEL
    disponiveis = sum(1 for f in fontes if f.dados_disponiveis)
    ratio = disponiveis / len(fontes)
    if ratio >= 0.8: return NivelConfianca.ALTO
    if ratio >= 0.5: return NivelConfianca.MEDIO
    return NivelConfianca.BAIXO


# ─── Módulo cards (JSON mode) ────────────────────────────────────────────────

_CARD_SYSTEM = """Gere um card de conteúdo para redes sociais. Retorne APENAS JSON válido:
{
  "titulo": "string — impactante, máx 8 palavras",
  "subtitulo": "string — complemento, máx 12 palavras, ou null",
  "corpo": "string — texto principal, máx 35 palavras, direto",
  "cta": "string — chamada para ação, máx 5 palavras",
  "hashtags": ["string", "string", "string"]
}
Regras: nunca invente dados. Use apenas informações fornecidas pelo usuário ou dados verificáveis.
Linguagem: português do Brasil, tom profissional e acessível."""


async def _gerar_card(mensagem: str, historico: list) -> dict:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    data_coleta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    messages = [
        {"role": "system", "content": _CARD_SYSTEM},
        *[{"role": m["role"], "content": m["content"]} for m in historico[-4:]],
        {"role": "user", "content": mensagem},
    ]

    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=400,
    )

    card_data = json.loads(response.choices[0].message.content)

    # Texto legível para exibição no chat
    hashtags = " ".join(card_data.get("hashtags", []))
    subtitulo = f"\n*{card_data['subtitulo']}*" if card_data.get("subtitulo") else ""
    resposta = (
        f"## {card_data.get('titulo', '')}"
        f"{subtitulo}\n\n"
        f"{card_data.get('corpo', '')}\n\n"
        f"**→ {card_data.get('cta', '')}**\n\n"
        f"`{hashtags}`\n\n"
        f"⚠️ Informação educativa. Não constitui assessoria profissional."
    )

    return {
        "resposta": resposta,
        "fontes": [],
        "data_coleta": data_coleta,
        "nivel_confianca": NivelConfianca.ALTO,
        "observacoes": None,
        "dados_coletados": None,
        "card_data": card_data,
    }


# ─── Função principal ────────────────────────────────────────────────────────

async def processar_mensagem(mensagem: str, historico: list, modulo: str = "geral") -> dict:
    """
    Processa mensagem do usuário.
    - modulo="cards": usa JSON mode, retorna card_data
    - demais módulos: usa function calling com APIs oficiais
    """
    if modulo == "cards":
        return await _gerar_card(mensagem, historico)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    data_coleta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_prompt = SYSTEM_PROMPTS.get(modulo, SYSTEM_PROMPTS["geral"])

    # Módulos que não usam dados econômicos externos (apenas OpenAI)
    _MODULOS_SEM_TOOLS = {"nr1", "tributario", "assistentes"}
    usar_tools = modulo not in _MODULOS_SEM_TOOLS

    mensagens: list[dict] = (
        [{"role": "system", "content": system_prompt}]
        + historico
        + [{"role": "user", "content": mensagem}]
    )

    dados_coletados: dict[str, Any] = {}
    max_iter = 6

    for _ in range(max_iter):
        kwargs: dict[str, Any] = dict(
            model=MODEL,
            messages=mensagens,
            temperature=0.2,
            max_tokens=2048,
        )
        if usar_tools:
            kwargs["tools"] = TOOLS
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        escolha = response.choices[0]

        if escolha.finish_reason != "tool_calls":
            break

        mensagens.append(escolha.message.model_dump(exclude_unset=False))

        tool_calls = escolha.message.tool_calls or []
        resultados = await asyncio.gather(
            *[_executar_ferramenta(tc.function.name, json.loads(tc.function.arguments))
              for tc in tool_calls]
        )

        for tc, resultado in zip(tool_calls, resultados):
            dados_coletados[tc.function.name] = resultado
            mensagens.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(resultado, ensure_ascii=False, default=str),
            })

    resposta_texto = escolha.message.content or "Não foi possível gerar uma resposta."
    fontes = _extrair_fontes(mensagens)
    nivel_confianca = _calcular_confianca(fontes) if fontes else NivelConfianca.ALTO

    fontes_indisponiveis = [f.nome for f in fontes if not f.dados_disponiveis]
    observacoes = (
        f"Fonte(s) indisponível(is) no momento: {', '.join(fontes_indisponiveis)}. "
        "A resposta pode estar incompleta."
        if fontes_indisponiveis else None
    )

    return {
        "resposta": resposta_texto,
        "fontes": fontes,
        "data_coleta": data_coleta,
        "nivel_confianca": nivel_confianca,
        "observacoes": observacoes,
        "dados_coletados": dados_coletados if dados_coletados else None,
        "card_data": None,
    }
