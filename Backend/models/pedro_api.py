"""Registro isolado das rotas atribuídas a Pedro."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from models.pedro_comum import Conflito, NaoEncontrado
from models import pedro_itens as itens, pedro_qrcodes as qrcodes, pedro_tarefas as tarefas_execucao


def incluir_rotas(app: FastAPI) -> None:
    @app.exception_handler(NaoEncontrado)
    async def nao_encontrado(request: Request, exc: NaoEncontrado):
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(Conflito)
    async def conflito(request: Request, exc: Conflito):
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(SQLAlchemyError)
    async def erro_banco(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Banco indisponível ou schema incompatível."},
        )

    app.include_router(itens.router)
    app.include_router(qrcodes.router)
    app.include_router(tarefas_execucao.router)
