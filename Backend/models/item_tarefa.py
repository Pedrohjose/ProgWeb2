from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    Date,
    ForeignKey,
    String
)
from sqlalchemy.orm import relationship
from banco import Base


class StatusItemTarefa(str, Enum):
    PENDENTE = "Pendente"
    CONFERIDO = "Conferido"


class ItensTarefa(Base):
    __tablename__ = "ItensTarefa"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    statusItemTarefa = Column(
        String(20),
        nullable=False
    )

    dataConferencia = Column(
        Date,
        nullable=False
    )

    id_tarefa = Column(
        Integer,
        ForeignKey(
            "Tarefas.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    tarefa = relationship(
        "Tarefa",
        back_populates="itens_tarefa"
    )

    itens = relationship(
        "Item",
        back_populates="item_tarefa"
    )
