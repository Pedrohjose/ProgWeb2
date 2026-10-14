from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from banco import Base


class StatusTarefa(str, Enum):
    PENDENTE = "Pendante"
    EM_ANDAMENTO = "Em_Andamento"
    CONCLUIDA = "Concluida"


class Tarefa(Base):
    __tablename__ = "Tarefas"

    id = Column(Integer, primary_key=True, autoincrement=True)

    tituto = Column(
        String(255),
        nullable=False,
        unique=True
    )

    descricao = Column(
        String(255),
        nullable=True
    )

    dataCadastro = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    prazo = Column(
        Date,
        nullable=False
    )

    statusTarefas = Column(
        String(20),
        nullable=False
    )

    id_usuario = Column(
        Integer,
        ForeignKey(
            "Usuarios.id",
            ondelete="CASCADE"
        ),
        nullable=True
    )

    usuario = relationship(
        "Usuario",
        back_populates="tarefas"
    )

    itens_tarefa = relationship(
        "ItensTarefa",
        back_populates="tarefa",
        cascade="all, delete"
    )
