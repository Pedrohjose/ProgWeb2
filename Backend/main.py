from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from banco import get_db
from routers import auth, localizacoes, tarefas_gestao, usuarios
from models.pedro_api import incluir_rotas
from schemas import Saude, respostas

DESCRICAO = """
Documentação e testes da API do sistema de gerenciamento de patrimônio **ESTOK**.

**Os 20 endpoints do escopo estão implementados:** login, usuários, localizações e gestão de tarefas.
As duas rotas de diagnóstico são auxiliares e não entram nessa contagem.

### Roteiro de teste
1. Cadastre um usuário em **POST /usuarios** e guarde o `id`.
2. Teste **POST /login** com o email e a senha cadastrados.
3. Cadastre uma localização em **POST /localizacoes**.
4. Crie uma tarefa em **POST /tarefas**, edite em **PUT /tarefas/{id}** e atribua ao usuário em **PUT /tarefas/{id}/atribuir/{usuarioId}**.
5. Confira **GET /usuarios/{id}/tarefas/all**, depois exclua tarefa, localização e usuário de teste (204) e consulte de novo (404).

**Ambiente acadêmico de desenvolvimento:** login valida as credenciais, mas ainda
não emite token. As rotas não exigem autenticação ou autorização nesta etapa.
Use dados de teste.
"""
app = FastAPI(
    title="ESTOK — Swagger de Testes",
    summary="API REST do projeto ESTOK — autenticação, usuários, localizações e tarefas",
    version="0.3.0",
    description=DESCRICAO,
    openapi_tags=[
        {"name": "Autenticação", "description": "Validação de email e senha de usuário cadastrado."},
        {"name": "Usuários", "description": "Cadastro, listagem, consulta, atualização e exclusão de usuários; tarefas do usuário."},
        {"name": "Localizações", "description": "CRUD de localizações, itens armazenados e QR Codes."},
        {"name": "Tarefas - Gestão", "description": "Criação, edição, exclusão e atribuição de tarefas."},
        {"name": "Diagnóstico", "description": "Verificação da API e da conexão com o banco; rotas auxiliares."},
    ],
    swagger_ui_parameters={"docExpansion": "list", "displayRequestDuration": True},
)
incluir_rotas(app)


@app.exception_handler(SQLAlchemyError)
async def erro_banco(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Banco indisponível ou schema incompatível. Verifique a configuração e as migrations."})


@app.get("/saude", tags=["Diagnóstico"], response_model=Saude, summary="Verificar se a API está ativa")
def saude():
    return {"status": "ok"}


@app.get("/saude/banco", tags=["Diagnóstico"], response_model=Saude, responses=respostas(),
         summary="Verificar a conexão com MySQL")
def saude_banco(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


for router in (auth.router, usuarios.router, localizacoes.router, tarefas_gestao.router):
    app.include_router(router)
