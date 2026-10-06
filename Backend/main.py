from enum import Enum
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from banco import get_db
from models import Usuario, Tarefa
from seguranca import hash_senha, verificar_senha

DESCRICAO = """
Documentação e testes da API do sistema de gerenciamento de patrimônio **ESTOK**.

**6 dos 20 endpoints previstos estão implementados:** login e CRUD de usuários.
As duas rotas de diagnóstico são auxiliares e não entram nessa contagem.

### Roteiro de teste
1. Cadastre um usuário em **POST /usuarios** e guarde o `id` retornado.
2. Teste **POST /login** com o email e a senha cadastrados.
3. Liste os usuários, consulte o `id`, atualize o cadastro e exclua o usuário de teste.
4. Consulte novamente o `id` excluído para verificar a resposta **404**.

**Ambiente acadêmico de desenvolvimento:** login valida as credenciais, mas ainda
não emite token. As rotas não exigem autenticação ou autorização nesta etapa.
Use dados de teste. Tarefas, localizações e consulta de tarefas por usuário
continuam pendentes para a próxima etapa do projeto.
"""
app = FastAPI(
    title="ESTOK — Swagger de Testes",
    summary="API REST do projeto ESTOK — autenticação e usuários",
    version="0.2.0",
    description=DESCRICAO,
    openapi_tags=[
        {"name": "Autenticação", "description": "Validação de email e senha de usuário cadastrado."},
        {"name": "Usuários", "description": "Cadastro, listagem, consulta, atualização e exclusão de usuários."},
        {"name": "Diagnóstico", "description": "Verificação da API e da conexão com o banco; rotas auxiliares."},
    ],
    swagger_ui_parameters={"docExpansion": "list", "displayRequestDuration": True},
)

class Erro(BaseModel):
    detail: str
class Perfil(str, Enum):
    admin = "Admin"
    funcionario = "Funcionario"
class UsuarioEntrada(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "nome": "Usuário de Teste", "email": "teste@example.com",
        "senha": "TesteLocal123!", "perfil": "Funcionario"
    }]})
    nome: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    senha: str = Field(min_length=8, max_length=128, description="Senha da aplicação (não é a senha do MySQL).", json_schema_extra={"writeOnly": True})
    perfil: Perfil
class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [{
        "id": 1, "nome": "Usuário de Teste", "email": "teste@example.com", "perfil": "Funcionario"
    }]})
    id: int
    nome: str
    email: str
    perfil: Perfil
class Login(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"email": "teste@example.com", "senha": "TesteLocal123!"}]})
    email: str
    senha: str = Field(json_schema_extra={"writeOnly": True})
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
    responses={503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Verificar a conexão com MySQL")
def saude_banco(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.post("/usuarios", tags=["Usuários"], status_code=201, response_model=UsuarioSaida,
    responses={409: {"model": Erro, "description": "Dados em conflito ou usuário com vínculos."}, 503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Cadastrar usuário", description="Item 10 da lista. Persiste o cadastro e retorna 201 com o ID. Email duplicado retorna 409. A senha é armazenada em hash e não é retornada.")
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
    responses={404: {"model": Erro, "description": "Usuário não encontrado."}, 409: {"model": Erro, "description": "Dados em conflito ou usuário com vínculos."}, 503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Atualizar usuário", description="Item 11 da lista. Substitui nome, email, senha e perfil do usuário indicado. Envie todos os campos. Retorna 404 se o ID não existir e 409 em caso de conflito de email.")
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
    responses={401: {"model": Erro, "description": "Email ou senha inválidos."}, 503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Validar email e senha", description="Item 1 da lista. Retorna 200 e os dados públicos do usuário ou 401 se as credenciais forem inválidas. Não gera token nesta etapa.")
def login(dados: Login, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha):
        raise HTTPException(401, "Email ou senha inválidos.")
    return {"mensagem": "Login realizado com sucesso", "usuario": usuario}


# Registrar /all antes de /{id}: all é um segmento fixo, não um parâmetro.
@app.get("/usuarios/all", tags=["Usuários"], response_model=list[UsuarioSaida],
    responses={503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Listar usuários",
    description="Item 8 da lista, originalmente escrito /usuarios/{all}. A palavra all é fixa nesta implementação. Retorna os usuários por ID crescente, sem senhas; retorna [] se não houver cadastros.")
def listar_usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.id)).all()


@app.get("/usuarios/{id}", tags=["Usuários"], response_model=UsuarioSaida,
    responses={404: {"model": Erro, "description": "Usuário não encontrado."}, 503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Consultar usuário por ID",
    description="Item 9 da lista. Retorna os dados públicos do usuário. ID inexistente retorna 404; ID não inteiro retorna 422.")
def consultar_usuario(id: int, db: Session = Depends(get_db)):
    usuario = db.get(Usuario, id)
    if usuario is None:
        raise HTTPException(404, "Usuário não encontrado.")
    return usuario


@app.delete("/usuarios/{id}", tags=["Usuários"], status_code=204, response_class=Response,
    responses={404: {"model": Erro, "description": "Usuário não encontrado."}, 409: {"model": Erro, "description": "Dados em conflito ou usuário com vínculos."}, 503: {"model": Erro, "description": "Banco indisponível ou schema incompatível."}}, summary="Excluir usuário",
    description="Item 12 da lista. Exclui definitivamente o usuário e retorna 204 sem conteúdo. ID inexistente retorna 404. Usuário com tarefas vinculadas retorna 409; essas tarefas precisam ser tratadas antes da exclusão.")
def excluir_usuario(id: int, db: Session = Depends(get_db)):
    usuario = db.get(Usuario, id)
    if usuario is None:
        raise HTTPException(404, "Usuário não encontrado.")
    if db.scalar(select(Tarefa.id).where(Tarefa.id_usuario == id).limit(1)) is not None:
        raise HTTPException(409, "Usuário possui tarefas vinculadas e não pode ser excluído.")
    db.delete(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Usuário possui vínculos que impedem a exclusão.")
    return Response(status_code=204)
