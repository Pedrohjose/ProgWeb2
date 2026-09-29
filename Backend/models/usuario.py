from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from enum import Enum
from banco import Base


class PerfilUsuario(str, Enum):
    ADMIN = "Admin"
    FUNCIONARIO = "Funcionario"


class Usuario(Base):
    __tablename__ = "Usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    senha = Column(String(255), nullable=False)
    perfil = Column(String(20), nullable=False)

    tarefas = relationship(
        "Tarefa",
        back_populates="usuario",
        cascade="all, delete"
    )

