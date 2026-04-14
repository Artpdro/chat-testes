"""
Serviço de integração com o Portal da Transparência do Governo Federal.
API: https://api.portaldatransparencia.gov.br/api-de-dados/
Requer chave de API (cadastro gratuito em portaldatransparencia.gov.br).
Quando a chave não está configurada, retorna dados explicativos.
"""
import httpx
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"


def _headers() -> dict:
    chave = os.getenv("TRANSPARENCIA_API_KEY", "")
    if not chave:
        return {}
    return {"chave-api-dados": chave}


def _chave_configurada() -> bool:
    return bool(os.getenv("TRANSPARENCIA_API_KEY", "").strip())


async def buscar_despesas(ano: int | None = None, mes: int | None = None) -> dict:
    """
    Busca despesas do governo federal por período.
    Endpoint: /despesas/por-orgao
    """
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not _chave_configurada():
        return _resposta_sem_chave("despesas", data_consulta)

    hoje = datetime.now()
    ano = ano or hoje.year
    mes = mes or hoje.month

    url = f"{BASE_URL}/despesas/recursos-por-funcao"
    params = {"ano": ano, "mes": mes, "pagina": 1}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params, headers=_headers())
            response.raise_for_status()
            dados = response.json()

        return {
            "disponivel": True,
            "tipo": "despesas",
            "ano": ano,
            "mes": mes,
            "data_consulta": data_consulta,
            "fonte": "Portal da Transparência – Gov Federal",
            "url": "https://portaldatransparencia.gov.br/despesas",
            "total_registros": len(dados) if isinstance(dados, list) else 1,
            "dados": dados[:20] if isinstance(dados, list) else dados,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return _resposta_sem_chave("despesas", data_consulta, chave_invalida=True)
        logger.warning("Transparência HTTP %s para despesas", e.response.status_code)
        return _resposta_vazia("despesas", data_consulta, f"HTTP {e.response.status_code}")
    except Exception as e:
        logger.warning("Transparência falhou para despesas: %s", e)
        return _resposta_vazia("despesas", data_consulta, str(e))


async def buscar_receitas(ano: int | None = None, mes: int | None = None) -> dict:
    """Busca receitas do governo federal."""
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not _chave_configurada():
        return _resposta_sem_chave("receitas", data_consulta)

    hoje = datetime.now()
    ano = ano or hoje.year
    mes = mes or hoje.month

    url = f"{BASE_URL}/receitas/por-orgao"
    params = {"ano": ano, "mes": mes, "pagina": 1}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params, headers=_headers())
            response.raise_for_status()
            dados = response.json()

        return {
            "disponivel": True,
            "tipo": "receitas",
            "ano": ano,
            "mes": mes,
            "data_consulta": data_consulta,
            "fonte": "Portal da Transparência – Gov Federal",
            "url": "https://portaldatransparencia.gov.br/receitas",
            "total_registros": len(dados) if isinstance(dados, list) else 1,
            "dados": dados[:20] if isinstance(dados, list) else dados,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return _resposta_sem_chave("receitas", data_consulta, chave_invalida=True)
        return _resposta_vazia("receitas", data_consulta, f"HTTP {e.response.status_code}")
    except Exception as e:
        return _resposta_vazia("receitas", data_consulta, str(e))


async def buscar_licitacoes(uf: str | None = None, ano: int | None = None) -> dict:
    """Busca licitações do governo federal."""
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not _chave_configurada():
        return _resposta_sem_chave("licitacoes", data_consulta)

    hoje = datetime.now()
    ano = ano or hoje.year

    url = f"{BASE_URL}/licitacoes"
    params = {"dataInicial": f"01/01/{ano}", "dataFinal": f"31/12/{ano}", "pagina": 1}
    if uf:
        params["uf"] = uf.upper()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params, headers=_headers())
            response.raise_for_status()
            dados = response.json()

        return {
            "disponivel": True,
            "tipo": "licitacoes",
            "ano": ano,
            "uf": uf,
            "data_consulta": data_consulta,
            "fonte": "Portal da Transparência – Gov Federal",
            "url": "https://portaldatransparencia.gov.br/licitacoes",
            "total_registros": len(dados) if isinstance(dados, list) else 1,
            "dados": dados[:20] if isinstance(dados, list) else dados,
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return _resposta_sem_chave("licitacoes", data_consulta, chave_invalida=True)
        return _resposta_vazia("licitacoes", data_consulta, f"HTTP {e.response.status_code}")
    except Exception as e:
        return _resposta_vazia("licitacoes", data_consulta, str(e))


def _resposta_sem_chave(tipo: str, data_consulta: str, chave_invalida: bool = False) -> dict:
    msg = (
        "Chave de API inválida ou expirada. Verifique TRANSPARENCIA_API_KEY."
        if chave_invalida
        else (
            "Chave de API não configurada. Cadastre-se gratuitamente em "
            "https://portaldatransparencia.gov.br/api-de-dados e configure "
            "TRANSPARENCIA_API_KEY no .env para acessar dados do Portal da Transparência."
        )
    )
    return {
        "disponivel": False,
        "tipo": tipo,
        "data_consulta": data_consulta,
        "fonte": "Portal da Transparência – Gov Federal",
        "url": "https://portaldatransparencia.gov.br/api-de-dados",
        "erro": msg,
        "instrucoes": "Configure a variável TRANSPARENCIA_API_KEY no arquivo .env",
    }


def _resposta_vazia(tipo: str, data_consulta: str, motivo: str) -> dict:
    return {
        "disponivel": False,
        "tipo": tipo,
        "data_consulta": data_consulta,
        "fonte": "Portal da Transparência – Gov Federal",
        "url": "https://portaldatransparencia.gov.br",
        "erro": motivo,
    }
