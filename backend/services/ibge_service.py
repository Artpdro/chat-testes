"""
Serviço de integração com o IBGE.
APIs públicas:
  - SIDRA (tabelas agregadas): https://servicodados.ibge.gov.br/api/v3/
  - IBGE Indicadores: https://servicodados.ibge.gov.br/api/v1/indicadores
Não requerem autenticação.
"""
import httpx
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

SIDRA_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Configurações dos agregados SIDRA mais usados
AGREGADOS = {
    "ipca": {
        "id": 1737,
        "variaveis": "63",
        "periodos": "12",
        "localidades": "N1[all]",
        "nome": "IPCA – Variação mensal",
        "unidade": "% a.m.",
        "descricao": "Índice Nacional de Preços ao Consumidor Amplo",
    },
    "ipca_acumulado_12m": {
        "id": 1737,
        "variaveis": "2266",
        "periodos": "4",
        "localidades": "N1[all]",
        "nome": "IPCA – Acumulado 12 meses",
        "unidade": "%",
        "descricao": "IPCA acumulado nos últimos 12 meses",
    },
    "pib_trimestral": {
        "id": 5932,
        "variaveis": "6564",
        "periodos": "8",
        "localidades": "N1[all]",
        "nome": "PIB Trimestral – Taxa de crescimento",
        "unidade": "%",
        "descricao": "Taxa de crescimento do PIB em relação ao trimestre anterior",
    },
    "pib_acumulado": {
        "id": 5932,
        "variaveis": "6561",
        "periodos": "8",
        "localidades": "N1[all]",
        "nome": "PIB – Valores correntes (R$ mil)",
        "unidade": "R$ mil",
        "descricao": "PIB a preços de mercado em valores correntes",
    },
    "desemprego": {
        "id": 6381,
        "variaveis": "4099",
        "periodos": "8",
        "localidades": "N1[all]",
        "nome": "Taxa de Desemprego – PNAD Contínua",
        "unidade": "%",
        "descricao": "Taxa de desocupação da população em idade ativa",
    },
    "inpc": {
        "id": 1736,
        "variaveis": "44",
        "periodos": "12",
        "localidades": "N1[all]",
        "nome": "INPC – Variação mensal",
        "unidade": "% a.m.",
        "descricao": "Índice Nacional de Preços ao Consumidor",
    },
    "populacao": {
        "id": 6579,
        "variaveis": "93",
        "periodos": "1",
        "localidades": "N1[all]",
        "nome": "População Estimada",
        "unidade": "pessoas",
        "descricao": "Estimativa da população total do Brasil",
    },
}


async def buscar_indicador(indicador: str) -> dict:
    """Busca um indicador do IBGE via SIDRA."""
    indicador_lower = indicador.lower()
    if indicador_lower not in AGREGADOS:
        return {
            "disponivel": False,
            "erro": f"Indicador '{indicador}' não mapeado. Disponíveis: {', '.join(AGREGADOS.keys())}",
        }

    cfg = AGREGADOS[indicador_lower]
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = (
        f"{SIDRA_BASE}/{cfg['id']}/periodos/-{cfg['periodos']}"
        f"/variaveis/{cfg['variaveis']}"
        f"?localidades={cfg['localidades']}&classificacao="
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            dados_raw = response.json()

        resultados = _parsear_sidra(dados_raw)

        return {
            "disponivel": True,
            "indicador": indicador_lower,
            "nome": cfg["nome"],
            "unidade": cfg["unidade"],
            "descricao": cfg["descricao"],
            "data_consulta": data_consulta,
            "fonte": "IBGE – SIDRA",
            "url": f"https://sidra.ibge.gov.br/tabela/{cfg['id']}",
            "dados": resultados,
            "ultimo_valor": resultados[-1]["valor"] if resultados else None,
            "ultimo_periodo": resultados[-1]["periodo"] if resultados else None,
        }

    except httpx.HTTPStatusError as e:
        logger.warning("IBGE SIDRA HTTP %s para %s", e.response.status_code, indicador)
        return _resposta_vazia(indicador_lower, cfg, data_consulta, f"HTTP {e.response.status_code}")
    except (httpx.RequestError, KeyError, IndexError) as e:
        logger.warning("IBGE SIDRA falhou para %s: %s", indicador, e)
        return _resposta_vazia(indicador_lower, cfg, data_consulta, str(e))


def _parsear_sidra(dados_raw: list) -> list:
    """Extrai período e valor do formato padrão do SIDRA."""
    resultados = []
    for bloco in dados_raw:
        for item in bloco.get("resultados", []):
            for serie_dict in item.get("series", []):
                for periodo, valor in serie_dict.get("serie", {}).items():
                    resultados.append({
                        "periodo": _formatar_periodo(periodo),
                        "valor": valor if valor != "..." else None,
                    })
    return resultados


def _formatar_periodo(periodo: str) -> str:
    """Converte '202401' → 'Jan/2024', '20241' → '1º trim/2024'."""
    if len(periodo) == 6:  # AAAAMM
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                 "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        try:
            ano, mes = int(periodo[:4]), int(periodo[4:])
            return f"{meses[mes - 1]}/{ano}"
        except (ValueError, IndexError):
            return periodo
    if len(periodo) == 5:  # AAAAT (trimestre)
        try:
            ano, trim = int(periodo[:4]), int(periodo[4:])
            return f"{trim}º tri/{ano}"
        except ValueError:
            return periodo
    return periodo


def _resposta_vazia(indicador: str, cfg: dict, data_consulta: str, motivo: str) -> dict:
    return {
        "disponivel": False,
        "indicador": indicador,
        "nome": cfg.get("nome", indicador),
        "data_consulta": data_consulta,
        "fonte": "IBGE – SIDRA",
        "url": f"https://sidra.ibge.gov.br/tabela/{cfg.get('id', '')}",
        "erro": motivo,
    }
