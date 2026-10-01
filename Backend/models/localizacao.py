from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    func
)
from sqlalchemy.orm import relationship
from banco import Base


class TipoEndereco(str, Enum):
    RESIDENCIAL = "Residencial"
    COMERCIAL = "Comercial"
    ENTREGA = "Entrega"
    COBRANCA = "Cobranca"


class Localizacao(Base):
    __tablename__ = "Localizacoes"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nome = Column(
        String(255),
        nullable=False
    )

    cep = Column(
        String(8),
        nullable=False
    )

    logradouro = Column(
        String(255),
        nullable=False
    )

    numero = Column(
        String(20),
        nullable=False
    )

    complemento = Column(
        String(100),
        nullable=True
    )

    bairro = Column(
        String(100),
        nullable=False
    )

    cidade = Column(
        String(100),
        nullable=False
    )

    estado = Column(
        String(2),
        nullable=False
    )

    latitude = Column(
        Numeric(10, 8),
        nullable=True
    )

    longitude = Column(
        Numeric(11, 8),
        nullable=True
    )

    tipo_endereco = Column(
        String(20),
        nullable=True,
        default="Entrega"
    )

    principal = Column(
        Boolean,
        default=False
    )

    dataCadastro = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    itens = relationship(
        "Item",
        back_populates="localizacao",
        cascade="all, delete"
    )
