"""
Serviço de integração com o Banco Central do Brasil.
API pública SGS (Sistema Gerenciador de Séries Temporais): https://api.bcb.gov.br
Não requer autenticação.
"""
import httpx
from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

# Mapa de séries disponíveis no SGS
SERIES = {
    "selic": {"codigo": 11, "nome": "Taxa SELIC (% a.a.)", "unidade": "% a.a."},
    "cdi": {"codigo": 12, "nome": "Taxa CDI (% a.a.)", "unidade": "% a.a."},
    "ipca": {"codigo": 433, "nome": "IPCA (% ao mês)", "unidade": "% a.m."},
    "igpm": {"codigo": 189, "nome": "IGP-M (% ao mês)", "unidade": "% a.m."},
    "usd_compra": {"codigo": 1, "nome": "Câmbio USD/BRL (compra)", "unidade": "R$"},
    "usd_venda": {"codigo": 10813, "nome": "Câmbio USD/BRL (venda)", "unidade": "R$"},
    "pib_mensal": {"codigo": 4380, "nome": "PIB Mensal (R$ milhões)", "unidade": "R$ milhões"},
    "selic_meta": {"codigo": 432, "nome": "Meta da Taxa SELIC (% a.a.)", "unidade": "% a.a."},
    "dolar_ptax": {"codigo": 3698, "nome": "Dólar PTAX (R$)", "unidade": "R$"},
    "euro_ptax": {"codigo": 21619, "nome": "Euro PTAX (R$)", "unidade": "R$"},
    "inpc": {"codigo": 188, "nome": "INPC (% ao mês)", "unidade": "% a.m."},
    "inadimplencia": {"codigo": 21082, "nome": "Inadimplência PF (% carteira)", "unidade": "%"},
}


async def buscar_serie(codigo_serie: int, ultimos_n: int = 12) -> dict:
    """
    Busca série temporal do SGS/BCB pelo código numérico.
    Retorna os últimos N registros disponíveis.
    """
    url = f"{BASE_URL}.{codigo_serie}/dados/ultimos/{ultimos_n}?formato=json"
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta = _meta_por_codigo(codigo_serie)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            dados = response.json()

        if not dados:
            return _resposta_vazia(codigo_serie, meta, data_consulta, "Série sem dados disponíveis")

        return {
            "disponivel": True,
            "codigo": codigo_serie,
            "nome": meta["nome"],
            "unidade": meta["unidade"],
            "data_consulta": data_consulta,
            "fonte": "Banco Central do Brasil – SGS",
            "url": f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados",
            "dados": dados,
            "ultimo_valor": dados[-1]["valor"] if dados else None,
            "ultima_data": dados[-1]["data"] if dados else None,
            "total_registros": len(dados),
        }

    except httpx.HTTPStatusError as e:
        logger.warning("BCB SGS HTTP %s para série %s", e.response.status_code, codigo_serie)
        return _resposta_vazia(codigo_serie, meta, data_consulta, f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        logger.warning("BCB SGS falhou para série %s: %s", codigo_serie, e)
        return _resposta_vazia(codigo_serie, meta, data_consulta, "Falha na conexão")


async def buscar_serie_por_nome(nome: str, ultimos_n: int = 12) -> dict:
    """Busca série pelo nome amigável (ex: 'selic', 'ipca', 'cdi')."""
    nome_lower = nome.lower()
    if nome_lower not in SERIES:
        return {
            "disponivel": False,
            "erro": f"Série '{nome}' não encontrada. Disponíveis: {', '.join(SERIES.keys())}",
        }
    meta = SERIES[nome_lower]
    return await buscar_serie(meta["codigo"], ultimos_n)


async def buscar_multiplas_series(nomes: list[str], ultimos_n: int = 6) -> dict:
    """Busca várias séries em paralelo e retorna um dicionário consolidado."""
    import asyncio
    tarefas = {nome: buscar_serie_por_nome(nome, ultimos_n) for nome in nomes}
    resultados = await asyncio.gather(*tarefas.values(), return_exceptions=True)
    return {nome: (r if not isinstance(r, Exception) else {"disponivel": False, "erro": str(r)})
            for nome, r in zip(tarefas.keys(), resultados)}


def _meta_por_codigo(codigo: int) -> dict:
    for meta in SERIES.values():
        if meta["codigo"] == codigo:
            return meta
    return {"nome": f"Série {codigo}", "unidade": ""}


def _resposta_vazia(codigo: int, meta: dict, data_consulta: str, motivo: str) -> dict:
    return {
        "disponivel": False,
        "codigo": codigo,
        "nome": meta["nome"],
        "unidade": meta["unidade"],
        "data_consulta": data_consulta,
        "fonte": "Banco Central do Brasil – SGS",
        "url": f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados",
        "erro": motivo,
    }
