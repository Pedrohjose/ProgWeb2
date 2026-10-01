from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pedro_api.erros import Conflito, NaoEncontrado
from models.item import Item
from pedro_api.repositories import itens as repo
from pedro_api.schemas import ItemEntrada


def listar(db: Session) -> list[Item]:
    return repo.listar(db)


def buscar(db: Session, item_id: int) -> Item:
    item = repo.buscar(db, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    return item


def _validar_localizacao(db: Session, localizacao_id: int | None) -> None:
    if localizacao_id is not None and not repo.localizacao_existe(db, localizacao_id):
        raise NaoEncontrado("Localização não encontrada")


def _salvar(db: Session, item: Item) -> Item:
    try:
        return repo.salvar(db, item)
    except IntegrityError as exc:
        db.rollback()
        raise Conflito("Código de item já cadastrado ou dados em conflito") from exc


def criar(db: Session, dados: ItemEntrada) -> Item:
    _validar_localizacao(db, dados.id_localizacao)
    return _salvar(db, Item(**dados.model_dump()))


def atualizar(db: Session, item_id: int, dados: ItemEntrada) -> Item:
    item = buscar(db, item_id)
    _validar_localizacao(db, dados.id_localizacao)
    for campo, valor in dados.model_dump().items():
        setattr(item, campo, valor)
    return _salvar(db, item)


def excluir(db: Session, item_id: int) -> None:
    repo.excluir(db, buscar(db, item_id))
