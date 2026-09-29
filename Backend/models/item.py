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
