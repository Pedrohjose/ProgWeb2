from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from banco import Base

from fastapi import APIRouter, Depends, Response, status
import pydantic
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm
from models.item_tarefa import ItensTarefa
from models.localizacao import Localizacao
from models.comum import NaoEncontrado, Conflito, Erro, get_db, PNGResponse

class Item(Base):
    __tablename__ = "Itens"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_itemTarefa = Column(
        Integer,
        ForeignKey(
            "ItensTarefa.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    id_localizacao = Column(
        Integer,
        ForeignKey(
            "Localizacoes.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    codigoUnico = Column(
        String(255),
        nullable=False,
        unique=True
    )

    nome = Column(
        String(255),
        nullable=False
    )

    descricao = Column(
        String(255),
        nullable=True
    )

    dataCadastro = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    item_tarefa = relationship(
        "ItensTarefa",
        back_populates="itens"
    )

    localizacao = relationship(
        "Localizacao",
        back_populates="itens"
    )


class ItemEntrada(pydantic.BaseModel):
    id_localizacao: int | None = None
    codigoUnico: str = pydantic.Field(min_length=1, max_length=255)
    nome: str = pydantic.Field(min_length=1, max_length=255)
    descricao: str | None = pydantic.Field(default=None, max_length=255)


class ItemSaida(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    id_itemTarefa: int | None
    id_localizacao: int | None
    codigoUnico: str
    nome: str
    descricao: str | None


def _repo_listar(db: sqlalchemy.orm.Session) -> list[Item]:
    return list(db.scalars(sqlalchemy.select(Item).order_by(Item.id)))


def _repo_buscar(db: sqlalchemy.orm.Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def _repo_buscar_por_codigo(db: sqlalchemy.orm.Session, codigo: str) -> Item | None:
    return db.scalar(sqlalchemy.select(Item).where(Item.codigoUnico == codigo))


def _repo_localizacao_existe(db: sqlalchemy.orm.Session, localizacao_id: int) -> bool:
    return db.get(Localizacao, localizacao_id) is not None


def _repo_salvar(db: sqlalchemy.orm.Session, item: Item) -> Item:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _repo_excluir(db: sqlalchemy.orm.Session, item: Item) -> None:
    vinculo_id = item.id_itemTarefa
    db.delete(item)
    db.flush()
    if vinculo_id is not None:
        restantes = db.scalar(sqlalchemy.select(Item.id).where(Item.id_itemTarefa == vinculo_id).limit(1))
        if restantes is None:
            vinculo = db.get(ItensTarefa, vinculo_id)
            if vinculo is not None:
                db.delete(vinculo)
    db.commit()


def _svc_listar(db: sqlalchemy.orm.Session) -> list[Item]:
    return _repo_listar(db)


def _svc_buscar(db: sqlalchemy.orm.Session, item_id: int) -> Item:
    item = _repo_buscar(db, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    return item


def _svc__validar_localizacao(db: sqlalchemy.orm.Session, localizacao_id: int | None) -> None:
    if localizacao_id is not None and not _repo_localizacao_existe(db, localizacao_id):
        raise NaoEncontrado("Localização não encontrada")


def _svc__salvar(db: sqlalchemy.orm.Session, item: Item) -> Item:
    try:
        return _repo_salvar(db, item)
    except sqlalchemy.exc.IntegrityError as exc:
        db.rollback()
        raise Conflito("Código de item já cadastrado ou dados em conflito") from exc


def _svc_criar(db: sqlalchemy.orm.Session, dados: ItemEntrada) -> Item:
    _svc__validar_localizacao(db, dados.id_localizacao)
    return _svc__salvar(db, Item(**dados.model_dump()))


def _svc_atualizar(db: sqlalchemy.orm.Session, item_id: int, dados: ItemEntrada) -> Item:
    item = _svc_buscar(db, item_id)
    _svc__validar_localizacao(db, dados.id_localizacao)
    for campo, valor in dados.model_dump().items():
        setattr(item, campo, valor)
    return _svc__salvar(db, item)


def _svc_excluir(db: sqlalchemy.orm.Session, item_id: int) -> None:
    _repo_excluir(db, _svc_buscar(db, item_id))


router = APIRouter(prefix="/itens", tags=["Itens"])

ERRO_404 = {404: {"model": Erro}, 503: {"model": Erro}}
ERRO_GRAVACAO = {404: {"model": Erro}, 409: {"model": Erro}, 503: {"model": Erro}}
RESPOSTA_PNG = {200: {"content": {"image/png": {}}}, 404: {"model": Erro}, 503: {"model": Erro}}


@router.get("/all", response_model=list[ItemSaida], responses={503: {"model": Erro}}, summary="Listar itens")
def listar_itens(db: sqlalchemy.orm.Session = Depends(get_db)):
    return _svc_listar(db)


@router.get("/{id}", response_model=ItemSaida, responses=ERRO_404, summary="Consultar item")
def obter_item(id: int, db: sqlalchemy.orm.Session = Depends(get_db)):
    return _svc_buscar(db, id)


@router.post("", response_model=ItemSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_GRAVACAO, summary="Cadastrar item")
def criar_item(dados: ItemEntrada, db: sqlalchemy.orm.Session = Depends(get_db)):
    return _svc_criar(db, dados)


@router.put("/{id}", response_model=ItemSaida, responses=ERRO_GRAVACAO, summary="Atualizar item")
def atualizar_item(id: int, dados: ItemEntrada, db: sqlalchemy.orm.Session = Depends(get_db)):
    return _svc_atualizar(db, id, dados)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               responses=ERRO_404, summary="Excluir item")
def excluir_item(id: int, db: sqlalchemy.orm.Session = Depends(get_db)):
    _svc_excluir(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/qrcode", response_class=PNGResponse,
            responses=RESPOSTA_PNG, summary="Consultar QR Code do item")
def obter_qrcode_item(id: int, db: sqlalchemy.orm.Session = Depends(get_db)):
    from models import qrcodes as qrcodes
    return PNGResponse(qrcodes._svc_imagem_do_item(db, id))


@router.post("/{id}/qrcode", response_class=PNGResponse, responses=RESPOSTA_PNG,
             summary="Gerar QR Code do item",
             description="Gera um PNG a partir do código único. O banco atual não armazena a imagem.")
def gerar_qrcode_item(id: int, db: sqlalchemy.orm.Session = Depends(get_db)):
    from models import qrcodes as qrcodes
    return PNGResponse(qrcodes._svc_imagem_do_item(db, id))
