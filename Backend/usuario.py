from fastapi import APIRouter
from pydantic import BaseModel

usuario_router = APIRouter()
id = 0;

class Usuario(BaseModel):
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
def adicinarUsuario(usuario: Usuario):
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
def atualizar_usuario(id: int, usuario: Usuario):

    print("ID:", id)
    print("Nome:", usuario.nome)
    print("Email:", usuario.email)
    print("Senha:", usuario.senha)
    print("Perfil:", usuario.perfil)

    return {
        "mensagem": "Usuário atualizado",
        "id": id
    }