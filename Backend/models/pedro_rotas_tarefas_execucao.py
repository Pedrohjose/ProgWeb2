from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from models.pedro_db import get_db
from models.pedro_schemas import Erro, EstadoTarefa, ItemTarefaSaida, ProgressoTarefa
from models import pedro_servico_tarefas_execucao as tarefas

router = APIRouter(prefix="/tarefas")

ERRO_404 = {404: {"model": Erro}, 503: {"model": Erro}}
ERRO_409 = {404: {"model": Erro}, 409: {"model": Erro}, 503: {"model": Erro}}


@router.post("/{id}/iniciar", tags=["Tarefas - Execução"], response_model=EstadoTarefa,
             responses=ERRO_409, summary="Iniciar tarefa")
def iniciar_tarefa(id: int, db: Session = Depends(get_db)):
    return tarefas.iniciar(db, id)


@router.post("/{id}/concluir", tags=["Tarefas - Execução"], response_model=EstadoTarefa,
             responses=ERRO_409, summary="Concluir tarefa")
def concluir_tarefa(id: int, db: Session = Depends(get_db)):
    return tarefas.concluir(db, id)


@router.get("/{id}/progresso", tags=["Tarefas - Execução"], response_model=ProgressoTarefa,
            responses=ERRO_404, summary="Consultar progresso da tarefa")
def progresso_tarefa(id: int, db: Session = Depends(get_db)):
    return tarefas.progresso(db, id)


@router.get("/{id}/itens/all", tags=["Tarefas - Itens"],
            response_model=list[ItemTarefaSaida], responses=ERRO_404,
            summary="Listar itens da tarefa")
def listar_itens_tarefa(id: int, db: Session = Depends(get_db)):
    return tarefas.listar_itens(db, id)


@router.get("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
            response_model=ItemTarefaSaida, responses=ERRO_404,
            summary="Consultar item da tarefa")
def obter_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    return tarefas.obter_item(db, id, itemId)


@router.post("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
             response_model=ItemTarefaSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_409, summary="Adicionar item à tarefa")
def adicionar_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    return tarefas.adicionar_item(db, id, itemId)


@router.delete("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
               status_code=status.HTTP_204_NO_CONTENT, responses=ERRO_404,
               summary="Remover item da tarefa")
def remover_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    tarefas.remover_item(db, id, itemId)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/itens/{itemId}/conferir", tags=["Tarefas - Itens"],
             response_model=ItemTarefaSaida, responses=ERRO_409,
             summary="Conferir item da tarefa")
def conferir_item(id: int, itemId: int, db: Session = Depends(get_db)):
    return tarefas.conferir_item(db, id, itemId)
