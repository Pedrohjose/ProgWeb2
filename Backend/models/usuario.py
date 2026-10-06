from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from enum import Enum
from banco import Base

usuario_router = APIRouter()
id = 0;

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

class UsuarioEntradaCarlos(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str

    def __init__(self, nome, email, senha, perfil):
        self.id = self.id + 1
        self.nome = nome
        self.email = email
        self.senha = senha
        self.perfil = perfil
        self.status = True

@usuario_router.post("/usuarios")
def adicinarUsuario(usuario: UsuarioEntradaCarlos):
    global id

    id += 1
    id_usuario = id

    print(usuario.nome)
    print(usuario.email)
    print(usuario.senha)
    print(usuario.perfil)

    return {
        "id": id_usuario,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil
    }

@usuario_router.put("PUT /usuarios/{id}")
def atualizar_usuario(id: int, usuario: UsuarioEntradaCarlos):

    print("ID:", id)
    print("Nome:", usuario.nome)
    print("Email:", usuario.email)
    print("Senha:", usuario.senha)
    print("Perfil:", usuario.perfil)

    return {
        "mensagem": "Usuário atualizado",
        "id": id
    }
