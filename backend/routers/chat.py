from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, ErroResponse
from services import openai_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

MODULOS_VALIDOS = {"geral", "diagnostico", "mercado", "tributario", "nr1", "cards", "assistentes"}


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={422: {"model": ErroResponse}, 500: {"model": ErroResponse}},
    summary="Envia mensagem ao chatbot",
)
async def chat(request: ChatRequest) -> ChatResponse:
    modulo = request.modulo if request.modulo in MODULOS_VALIDOS else "geral"

    historico = [{"role": msg.role, "content": msg.content} for msg in request.historico]

    try:
        resultado = await openai_service.processar_mensagem(
            mensagem=request.mensagem,
            historico=historico,
            modulo=modulo,
        )
    except Exception as e:
        logger.exception("Erro no processamento da mensagem")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

    return ChatResponse(**resultado)


@router.get("/modulos", summary="Lista os módulos disponíveis")
async def listar_modulos() -> dict:
    return {
        "modulos": [
            {"id": "geral",       "label": "Início",               "desc": "Visão geral de todos os módulos"},
            {"id": "diagnostico", "label": "Diagnóstico Empresarial", "desc": "Análise e recomendações personalizadas"},
            {"id": "mercado",     "label": "Pesquisa de Mercado",   "desc": "Nicho, oportunidades e riscos"},
            {"id": "tributario",  "label": "Reforma Tributária",    "desc": "Impacto no negócio e cronograma"},
            {"id": "nr1",         "label": "NR-1 e Compliance",     "desc": "Conformidade e riscos psicossociais"},
            {"id": "cards",       "label": "Gerador de Cards",      "desc": "Conteúdo visual para redes sociais"},
            {"id": "assistentes", "label": "Assistentes",           "desc": "Especialistas IA por área"},
        ]
    }


@router.get("/fontes", summary="Lista as fontes de dados integradas")
async def listar_fontes() -> dict:
    return {
        "fontes": [
            {"nome": "BCB/SGS", "url": "https://api.bcb.gov.br", "auth": "não requerida",
             "dados": ["SELIC", "CDI", "IPCA", "IGP-M", "Câmbio"]},
            {"nome": "IBGE/SIDRA", "url": "https://servicodados.ibge.gov.br", "auth": "não requerida",
             "dados": ["PIB", "Desemprego", "IPCA detalhado"]},
            {"nome": "CVM", "url": "https://dados.cvm.gov.br", "auth": "não requerida",
             "dados": ["Fundos", "Companhias Abertas"]},
            {"nome": "Portal da Transparência", "url": "https://api.portaldatransparencia.gov.br",
             "auth": "chave gratuita", "dados": ["Despesas", "Receitas", "Licitações"]},
        ]
    }
