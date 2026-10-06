from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.item import Item
from models.item_tarefa import ItensTarefa
from models.localizacao import Localizacao
from models.pedro_comum import Conflito, NaoEncontrado, Erro, PNGResponse, get_db


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


def _repo_listar(db: Session) -> list[Item]:
    return list(db.scalars(select(Item).order_by(Item.id)))


def _repo_buscar(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def _repo_buscar_por_codigo(db: Session, codigo: str) -> Item | None:
    return db.scalar(select(Item).where(Item.codigoUnico == codigo))


def _repo_localizacao_existe(db: Session, localizacao_id: int) -> bool:
    return db.get(Localizacao, localizacao_id) is not None


def _repo_salvar(db: Session, item: Item) -> Item:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _repo_excluir(db: Session, item: Item) -> None:
    vinculo_id = item.id_itemTarefa
    db.delete(item)
    db.flush()
    if vinculo_id is not None:
        restantes = db.scalar(select(Item.id).where(Item.id_itemTarefa == vinculo_id).limit(1))
        if restantes is None:
            vinculo = db.get(ItensTarefa, vinculo_id)
            if vinculo is not None:
                db.delete(vinculo)
    db.commit()


def _svc_listar(db: Session) -> list[Item]:
    return _repo_listar(db)


def _svc_buscar(db: Session, item_id: int) -> Item:
    item = _repo_buscar(db, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    return item


def _svc__validar_localizacao(db: Session, localizacao_id: int | None) -> None:
    if localizacao_id is not None and not _repo_localizacao_existe(db, localizacao_id):
        raise NaoEncontrado("Localização não encontrada")


def _svc__salvar(db: Session, item: Item) -> Item:
    try:
        return _repo_salvar(db, item)
    except IntegrityError as exc:
        db.rollback()
        raise Conflito("Código de item já cadastrado ou dados em conflito") from exc


def _svc_criar(db: Session, dados: ItemEntrada) -> Item:
    _svc__validar_localizacao(db, dados.id_localizacao)
    return _svc__salvar(db, Item(**dados.model_dump()))


def _svc_atualizar(db: Session, item_id: int, dados: ItemEntrada) -> Item:
    item = _svc_buscar(db, item_id)
    _svc__validar_localizacao(db, dados.id_localizacao)
    for campo, valor in dados.model_dump().items():
        setattr(item, campo, valor)
    return _svc__salvar(db, item)


def _svc_excluir(db: Session, item_id: int) -> None:
    _repo_excluir(db, _svc_buscar(db, item_id))


router = APIRouter(prefix="/itens", tags=["Itens"])

ERRO_404 = {404: {"model": Erro}, 503: {"model": Erro}}
ERRO_GRAVACAO = {404: {"model": Erro}, 409: {"model": Erro}, 503: {"model": Erro}}
RESPOSTA_PNG = {200: {"content": {"image/png": {}}}, 404: {"model": Erro}, 503: {"model": Erro}}


@router.get("/all", response_model=list[ItemSaida], responses={503: {"model": Erro}}, summary="Listar itens")
def listar_itens(db: Session = Depends(get_db)):
    return _svc_listar(db)


@router.get("/{id}", response_model=ItemSaida, responses=ERRO_404, summary="Consultar item")
def obter_item(id: int, db: Session = Depends(get_db)):
    return _svc_buscar(db, id)


@router.post("", response_model=ItemSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_GRAVACAO, summary="Cadastrar item")
def criar_item(dados: ItemEntrada, db: Session = Depends(get_db)):
    return _svc_criar(db, dados)


@router.put("/{id}", response_model=ItemSaida, responses=ERRO_GRAVACAO, summary="Atualizar item")
def atualizar_item(id: int, dados: ItemEntrada, db: Session = Depends(get_db)):
    return _svc_atualizar(db, id, dados)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               responses=ERRO_404, summary="Excluir item")
def excluir_item(id: int, db: Session = Depends(get_db)):
    _svc_excluir(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/qrcode", response_class=PNGResponse,
            responses=RESPOSTA_PNG, summary="Consultar QR Code do item")
def obter_qrcode_item(id: int, db: Session = Depends(get_db)):
    from models import pedro_qrcodes as qrcodes
    return PNGResponse(qrcodes._svc_imagem_do_item(db, id))


@router.post("/{id}/qrcode", response_class=PNGResponse, responses=RESPOSTA_PNG,
             summary="Gerar QR Code do item",
             description="Gera um PNG a partir do código único. O banco atual não armazena a imagem.")
def gerar_qrcode_item(id: int, db: Session = Depends(get_db)):
    from models import pedro_qrcodes as qrcodes
    return PNGResponse(qrcodes._svc_imagem_do_item(db, id))
