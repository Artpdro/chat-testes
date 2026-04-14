"""
Serviço de integração com a CVM (Comissão de Valores Mobiliários).
Dados Abertos CVM: https://dados.cvm.gov.br
Não requer autenticação.
"""
import httpx
import io
import csv
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

CVM_BASE = "https://dados.cvm.gov.br/dados"


async def buscar_fundos_resumo(filtro_nome: str = "", limite: int = 20) -> dict:
    """
    Busca cadastro de fundos de investimento registrados na CVM.
    Arquivo CSV público com dados cadastrais de todos os fundos.
    """
    url = f"{CVM_BASE}/FI/CAD/DADOS/cad_fi.csv"
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        # CSV em latin-1
        content = response.content.decode("latin-1")
        reader = csv.DictReader(io.StringIO(content), delimiter=";")

        fundos = []
        for row in reader:
            nome = row.get("DENOM_SOCIAL", "")
            if filtro_nome and filtro_nome.upper() not in nome.upper():
                continue
            situacao = row.get("SIT", "")
            if situacao not in ("EM FUNCIONAMENTO NORMAL",):
                continue
            fundos.append({
                "cnpj": row.get("CNPJ_FUNDO", ""),
                "nome": nome,
                "classe": row.get("CLASSE", ""),
                "tipo": row.get("TP_FUNDO", ""),
                "situacao": situacao,
                "data_inicio": row.get("DT_INI_ATIV", ""),
                "administrador": row.get("ADMIN", ""),
            })
            if len(fundos) >= limite:
                break

        return {
            "disponivel": True,
            "tipo": "fundos_cadastro",
            "data_consulta": data_consulta,
            "fonte": "CVM – Dados Abertos",
            "url": url,
            "total_retornado": len(fundos),
            "filtro_aplicado": filtro_nome or "(nenhum)",
            "dados": fundos,
        }

    except httpx.HTTPStatusError as e:
        logger.warning("CVM HTTP %s", e.response.status_code)
        return _resposta_vazia("fundos_cadastro", data_consulta, f"HTTP {e.response.status_code}")
    except Exception as e:
        logger.warning("CVM falhou: %s", e)
        return _resposta_vazia("fundos_cadastro", data_consulta, str(e))


async def buscar_cias_abertas(filtro_nome: str = "", limite: int = 20) -> dict:
    """
    Busca cadastro de companhias abertas registradas na CVM.
    """
    url = f"{CVM_BASE}/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    data_consulta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        content = response.content.decode("latin-1")
        reader = csv.DictReader(io.StringIO(content), delimiter=";")

        empresas = []
        for row in reader:
            nome = row.get("DENOM_SOCIAL", "")
            if filtro_nome and filtro_nome.upper() not in nome.upper():
                continue
            if row.get("SIT_REG", "") != "ATIVO":
                continue
            empresas.append({
                "cnpj": row.get("CNPJ_CIA", ""),
                "nome": nome,
                "nome_pregao": row.get("DENOM_COMERC", ""),
                "setor": row.get("SETOR_ATIV", ""),
                "situacao": row.get("SIT_REG", ""),
                "data_registro": row.get("DT_REG", ""),
                "pais": row.get("PAIS", ""),
            })
            if len(empresas) >= limite:
                break

        return {
            "disponivel": True,
            "tipo": "cias_abertas",
            "data_consulta": data_consulta,
            "fonte": "CVM – Dados Abertos",
            "url": url,
            "total_retornado": len(empresas),
            "filtro_aplicado": filtro_nome or "(nenhum)",
            "dados": empresas,
        }

    except httpx.HTTPStatusError as e:
        logger.warning("CVM cias HTTP %s", e.response.status_code)
        return _resposta_vazia("cias_abertas", data_consulta, f"HTTP {e.response.status_code}")
    except Exception as e:
        logger.warning("CVM cias falhou: %s", e)
        return _resposta_vazia("cias_abertas", data_consulta, str(e))


def _resposta_vazia(tipo: str, data_consulta: str, motivo: str) -> dict:
    return {
        "disponivel": False,
        "tipo": tipo,
        "data_consulta": data_consulta,
        "fonte": "CVM – Dados Abertos",
        "url": "https://dados.cvm.gov.br",
        "erro": motivo,
    }
