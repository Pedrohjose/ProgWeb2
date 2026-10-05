from sqlalchemy import select
from sqlalchemy.orm import Session

from models.item import Item
from models.item_tarefa import ItensTarefa
from models.localizacao import Localizacao


def listar(db: Session) -> list[Item]:
    return list(db.scalars(select(Item).order_by(Item.id)))


def buscar(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def buscar_por_codigo(db: Session, codigo: str) -> Item | None:
    return db.scalar(select(Item).where(Item.codigoUnico == codigo))


def localizacao_existe(db: Session, localizacao_id: int) -> bool:
    return db.get(Localizacao, localizacao_id) is not None


def salvar(db: Session, item: Item) -> Item:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def excluir(db: Session, item: Item) -> None:
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
