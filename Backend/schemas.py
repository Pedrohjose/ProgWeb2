"""Schemas Pydantic compartilhados pelos routers (entrada, saída e erros)."""
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from models.localizacao import TipoEndereco
from models.tarefa import StatusTarefa

SENHA_HASH = "A senha é armazenada em hash e nunca é retornada."
RESPOSTA_503 = {503: {"description": "Banco indisponível ou schema incompatível."}}


class Erro(BaseModel):
    detail: str


def respostas(*codigos):
    """Monta o bloco `responses` do Swagger para os códigos de erro informados."""
    textos = {
        401: "Email ou senha inválidos.",
        404: "Recurso não encontrado.",
        409: "Conflito com dados existentes ou vínculos que impedem a operação.",
        503: "Banco indisponível ou schema incompatível.",
    }
    return {c: {"model": Erro, "description": textos[c]} for c in (*codigos, 503)}


# ---------- Usuários e login ----------
class Perfil(str, Enum):
    admin = "Admin"
    funcionario = "Funcionario"


class UsuarioEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "nome": "Usuário de Teste", "email": "teste@example.com",
        "senha": "TesteLocal123!", "perfil": "Funcionario"}]})
    nome: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    senha: str = Field(min_length=8, max_length=128, description="Senha da aplicação (não é a senha do MySQL).",
                       json_schema_extra={"writeOnly": True})
    perfil: Perfil


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [{
        "id": 1, "nome": "Usuário de Teste", "email": "teste@example.com", "perfil": "Funcionario"}]})
    id: int
    nome: str
    email: str
    perfil: Perfil


class Login(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"email": "teste@example.com", "senha": "TesteLocal123!"}]})
    email: str
    senha: str = Field(json_schema_extra={"writeOnly": True})


class LoginSaida(BaseModel):
    mensagem: str
    usuario: UsuarioSaida


# ---------- Tarefas ----------
class TarefaAtualizacao(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "titulo": "Conferir estoque do almoxarifado", "descricao": "Contagem mensal",
        "prazo": "2026-12-01", "status": "Em_Andamento"}]})
    titulo: str = Field(min_length=1, max_length=255)
    descricao: str | None = Field(default=None, max_length=255)
    prazo: date
    status: StatusTarefa


class TarefaEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "titulo": "Conferir estoque do almoxarifado", "descricao": "Contagem mensal",
        "prazo": "2026-12-01", "status": "Pendante", "id_usuario": None}]})
    titulo: str = Field(min_length=1, max_length=255)
    descricao: str | None = Field(default=None, max_length=255)
    prazo: date
    status: StatusTarefa = StatusTarefa.PENDENTE
    id_usuario: int | None = Field(default=None, description="Funcionário responsável (opcional; também pode ser definido em PUT /tarefas/{id}/atribuir/{usuarioId}).")


class TarefaSaida(BaseModel):
    # No banco a coluna se chama `tituto` e `statusTarefas`; a API expõe nomes corretos.
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str = Field(validation_alias="tituto")
    descricao: str | None
    dataCadastro: datetime | None
    prazo: date
    status: StatusTarefa = Field(validation_alias="statusTarefas")
    id_usuario: int | None


# ---------- Localizações e itens ----------
class LocalizacaoEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "nome": "Almoxarifado Central", "cep": "01310100", "logradouro": "Avenida Paulista",
        "numero": "1000", "complemento": "Bloco B", "bairro": "Bela Vista", "cidade": "São Paulo",
        "estado": "SP", "latitude": -23.5614, "longitude": -46.6559,
        "tipo_endereco": "Comercial", "principal": False}]})
    nome: str = Field(min_length=1, max_length=255)
    cep: str = Field(pattern=r"^\d{8}$", description="8 dígitos, sem hífen.")
    logradouro: str = Field(min_length=1, max_length=255)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str = Field(min_length=1, max_length=100)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str = Field(pattern=r"^[A-Za-z]{2}$", description="Sigla da UF.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    tipo_endereco: TipoEndereco = TipoEndereco.ENTREGA
    principal: bool = False


class LocalizacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    cep: str
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    estado: str
    latitude: float | None
    longitude: float | None
    tipo_endereco: str | None
    principal: bool | None
    dataCadastro: datetime | None


class ItemSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigoUnico: str
    nome: str
    descricao: str | None
    dataCadastro: datetime | None
    id_localizacao: int | None


class QrCodeItem(BaseModel):
    item_id: int
    codigoUnico: str
    nome: str
    qrcode: str = Field(description="QR Code do `codigoUnico` como imagem SVG em data URI (use direto em <img src>).")


class Saude(BaseModel):
    status: str
