from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Erro(BaseModel):
    detail: str


class ItemEntrada(BaseModel):
    id_localizacao: int | None = None
    codigoUnico: str = Field(min_length=1, max_length=255)
    nome: str = Field(min_length=1, max_length=255)
    descricao: str | None = Field(default=None, max_length=255)


class ItemSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_itemTarefa: int | None
    id_localizacao: int | None
    codigoUnico: str
    nome: str
    descricao: str | None


class QRCodeSaida(BaseModel):
    codigo: str
    itemId: int
    url: str


class EstadoTarefa(BaseModel):
    mensagem: str
    id: int
    status: str


class ProgressoTarefa(BaseModel):
    tarefaId: int
    status: str
    totalItens: int
    itensConferidos: int
    itensPendentes: int
    percentual: float


class ItemTarefaSaida(BaseModel):
    id: int
    codigoUnico: str
    nome: str
    descricao: str | None
    status: str
    dataConferencia: date
