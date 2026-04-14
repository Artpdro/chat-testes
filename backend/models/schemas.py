from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum


class NivelConfianca(str, Enum):
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"
    INDISPONIVEL = "indisponivel"


class Fonte(BaseModel):
    nome: str
    url: str
    data_consulta: str
    dados_disponiveis: bool
    descricao: Optional[str] = None


class MensagemChat(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    mensagem: str = Field(..., min_length=1, max_length=2000)
    historico: List[MensagemChat] = Field(default_factory=list, max_length=20)
    modulo: str = Field(default="geral")


class ChatResponse(BaseModel):
    resposta: str
    fontes: List[Fonte]
    data_coleta: str
    nivel_confianca: NivelConfianca
    observacoes: Optional[str] = None
    dados_coletados: Optional[Dict[str, Any]] = None
    card_data: Optional[Dict[str, Any]] = None   # preenchido só no módulo "cards"


class ErroResponse(BaseModel):
    erro: str
    detalhe: Optional[str] = None
