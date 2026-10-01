from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.item import Item
from models.item_tarefa import ItensTarefa
from models.tarefa import Tarefa


def buscar_tarefa(db: Session, tarefa_id: int) -> Tarefa | None:
    return db.get(Tarefa, tarefa_id)


def itens_da_tarefa(db: Session, tarefa_id: int) -> list[tuple[Item, ItensTarefa]]:
    consulta = (
        select(Item, ItensTarefa)
        .join(ItensTarefa, Item.id_itemTarefa == ItensTarefa.id)
        .where(ItensTarefa.id_tarefa == tarefa_id)
        .order_by(Item.id)
    )
    return list(db.execute(consulta).all())


def vinculo_do_item(db: Session, item_id: int) -> tuple[Item, ItensTarefa] | None:
    consulta = (
        select(Item, ItensTarefa)
        .join(ItensTarefa, Item.id_itemTarefa == ItensTarefa.id)
        .where(Item.id == item_id)
    )
    return db.execute(consulta).first()


def contar_itens(db: Session, tarefa_id: int, status: str | None = None) -> int:
    consulta = (
        select(func.count(Item.id))
        .join(ItensTarefa, Item.id_itemTarefa == ItensTarefa.id)
        .where(ItensTarefa.id_tarefa == tarefa_id)
    )
    if status is not None:
        consulta = consulta.where(ItensTarefa.statusItemTarefa == status)
    return db.scalar(consulta) or 0


def salvar(db: Session, obj) -> None:
    db.add(obj)
    db.commit()


def adicionar_item(db: Session, item: Item, vinculo: ItensTarefa) -> ItensTarefa:
    db.add(vinculo)
    db.flush()
    item.id_itemTarefa = vinculo.id
    db.commit()
    db.refresh(vinculo)
    return vinculo


def remover_item(db: Session, item: Item, vinculo: ItensTarefa) -> None:
    item.id_itemTarefa = None
    db.flush()
    restantes = db.scalar(select(Item.id).where(Item.id_itemTarefa == vinculo.id).limit(1))
    if restantes is None:
        db.delete(vinculo)
    db.commit()
