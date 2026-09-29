from enum import Enum
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from banco import get_db
from models import Usuario
from seguranca import hash_senha, verificar_senha

app = FastAPI(title="ESTOK — João e Felipe", version="0.1.0",
    description="Base acadêmica: login, cadastro e atualização de usuários. As demais rotas da lista ainda precisam ser implementadas. Login valida credenciais, mas ainda não emite token nem protege as rotas.")

class Erro(BaseModel):
    detail: str
class Perfil(str, Enum):
    admin = "Admin"
    funcionario = "Funcionario"
class UsuarioEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    senha: str = Field(min_length=8, max_length=128)
    perfil: Perfil
class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: str
    perfil: Perfil
class Login(BaseModel):
    email: str
    senha: str
class LoginSaida(BaseModel):
    mensagem: str
    usuario: UsuarioSaida
class Saude(BaseModel):
    status: str

@app.exception_handler(SQLAlchemyError)
async def erro_banco(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Banco indisponível ou schema incompatível. Verifique a configuração e as migrations."})

@app.get("/saude", tags=["Diagnóstico"], response_model=Saude, summary="Verificar se a API está ativa")
def saude():
    return {"status": "ok"}

@app.get("/saude/banco", tags=["Diagnóstico"], response_model=Saude,
    responses={503: {"model": Erro}}, summary="Verificar a conexão com MySQL")
def saude_banco(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.post("/usuarios", tags=["Usuários"], status_code=201, response_model=UsuarioSaida,
    responses={409: {"model": Erro}, 503: {"model": Erro}}, summary="Cadastrar usuário")
def criar_usuario(dados: UsuarioEntrada, db: Session = Depends(get_db)):
    usuario = Usuario(nome=dados.nome, email=dados.email, senha=hash_senha(dados.senha), perfil=dados.perfil.value)
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email já cadastrado ou dados em conflito.")
    db.refresh(usuario)
    return usuario

@app.put("/usuarios/{id}", tags=["Usuários"], response_model=UsuarioSaida,
    responses={404: {"model": Erro}, 409: {"model": Erro}, 503: {"model": Erro}}, summary="Atualizar usuário")
def atualizar_usuario(id: int, dados: UsuarioEntrada, db: Session = Depends(get_db)):
    usuario = db.get(Usuario, id)
    if usuario is None:
        raise HTTPException(404, "Usuário não encontrado.")
    usuario.nome, usuario.email = dados.nome, dados.email
    usuario.senha, usuario.perfil = hash_senha(dados.senha), dados.perfil.value
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email já cadastrado ou dados em conflito.")
    db.refresh(usuario)
    return usuario

@app.post("/login", tags=["Autenticação"], response_model=LoginSaida,
    responses={401: {"model": Erro}, 503: {"model": Erro}}, summary="Validar email e senha")
def login(dados: Login, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha):
        raise HTTPException(401, "Email ou senha inválidos.")
    return {"mensagem": "Login realizado com sucesso", "usuario": usuario}
