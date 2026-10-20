"""Rotas de execução: funcionário atribuído executa; administradores gerenciam itens."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from banco import get_db
from models import tarefa as servicos
from models.comum import Erro
from permissoes_tarefas import tarefa_autorizada
from seguranca import exigir_roles

router = APIRouter(prefix="/tarefas", dependencies=[Depends(tarefa_autorizada)])
ERRO_404 = {401: {"model": Erro}, 403: {"model": Erro}, 404: {"model": Erro}, 503: {"model": Erro}}
ERRO_409 = {**ERRO_404, 409: {"model": Erro}}


@router.post("/{id}/iniciar", tags=["Tarefas - Execução"], response_model=servicos.EstadoTarefa,
             responses=ERRO_409, summary="Iniciar tarefa")
def iniciar_tarefa(id: int, db: Session = Depends(get_db)):
    return servicos._svc_iniciar(db, id)


@router.post("/{id}/concluir", tags=["Tarefas - Execução"], response_model=servicos.EstadoTarefa,
             responses=ERRO_409, summary="Concluir tarefa")
def concluir_tarefa(id: int, db: Session = Depends(get_db)):
    return servicos._svc_concluir(db, id)


@router.get("/{id}/progresso", tags=["Tarefas - Execução"], response_model=servicos.ProgressoTarefa,
            responses=ERRO_404, summary="Consultar progresso da tarefa")
def progresso_tarefa(id: int, db: Session = Depends(get_db)):
    return servicos._svc_progresso(db, id)


@router.get("/{id}/itens/all", tags=["Tarefas - Itens"],
            response_model=list[servicos.ItemTarefaSaida], responses=ERRO_404,
            summary="Listar itens da tarefa")
def listar_itens_tarefa(id: int, db: Session = Depends(get_db)):
    return servicos._svc_listar_itens(db, id)


@router.get("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
            response_model=servicos.ItemTarefaSaida, responses=ERRO_404,
            summary="Consultar item da tarefa")
def obter_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    return servicos._svc_obter_item(db, id, itemId)


@router.post("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
             response_model=servicos.ItemTarefaSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_409, summary="Adicionar item à tarefa",
             dependencies=[Depends(exigir_roles("Admin"))])
def adicionar_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    return servicos._svc_adicionar_item(db, id, itemId)


@router.delete("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
               status_code=status.HTTP_204_NO_CONTENT, responses=ERRO_404,
               summary="Remover item da tarefa", dependencies=[Depends(exigir_roles("Admin"))])
def remover_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    servicos._svc_remover_item(db, id, itemId)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/itens/{itemId}/conferir", tags=["Tarefas - Itens"],
             response_model=servicos.ItemTarefaSaida, responses=ERRO_409,
             summary="Conferir item da tarefa")
def conferir_item(id: int, itemId: int, db: Session = Depends(get_db)):
    return servicos._svc_conferir_item(db, id, itemId)
