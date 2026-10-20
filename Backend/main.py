from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from banco import get_db
from routers import auth, localizacoes, tarefas_gestao, usuarios
from models.api import incluir_rotas
from schemas import Saude, respostas
from seguranca import get_current_user

DESCRICAO = """
Documentação e testes da API do sistema de gerenciamento de patrimônio **ESTOK**.

Os endpoints do escopo acadêmico e os de autenticação estão documentados abaixo. As rotas
de diagnóstico são auxiliares e não entram nessa contagem.

### Roteiro de teste
1. Provisione o primeiro Admin conforme o README.
2. Faça **POST /login**, use o access token no botão **Authorize** e cadastre usuários em **POST /usuarios**.
3. Cadastre uma localização em **POST /localizacoes**.
4. Crie uma tarefa em **POST /tarefas**, edite em **PUT /tarefas/{id}** e atribua ao usuário em **PUT /tarefas/{id}/atribuir/{usuarioId}**.
5. Confira **GET /usuarios/{id}/tarefas/all**, depois exclua tarefa, localização e usuário de teste (204) e consulte de novo (404).

O login emite JWT de acesso e refresh token. Localizações e tarefas exigem Bearer token;
gestão de usuários, incluindo o cadastro, exige Admin ou Super Admin autenticado.
Super Admin é um papel próprio, tem todos os acessos de Admin e é o único que pode conceder
esse perfil ou alterar/excluir outra conta Super Admin.
Admin e Super Admin gerenciam localizações e tarefas e atribuem tarefas a funcionários ativos.
Funcionario consulta localizações e executa somente as tarefas atribuídas a ele.
Use dados de teste.
"""
app = FastAPI(
    title="ESTOK — Swagger de Testes",
    summary="API REST do projeto ESTOK — autenticação, usuários, localizações e tarefas",
    version="0.4.0",
    description=DESCRICAO,
    openapi_tags=[
        {"name": "Autenticação", "description": "Login, access tokens JWT, renovação rotativa e logout."},
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


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(localizacoes.router, dependencies=[Depends(get_current_user)])
app.include_router(tarefas_gestao.router, dependencies=[Depends(get_current_user)])
