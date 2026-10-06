from datetime import date
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.item import Item
from models.item_tarefa import ItensTarefa
from models.tarefa import Tarefa
from models.pedro_comum import Conflito, NaoEncontrado, Erro, get_db
from models import pedro_itens as itens


class EstadoTarefa(BaseModel):
    mensagem: str
    id: int
    status: str


class ProgressoTarefa(BaseModel):
    tarefaId: int
    status: str
    totalItens: int
    itensConferidos: int
    itensPendentes: int
    percentual: float


class ItemTarefaSaida(BaseModel):
    id: int
    codigoUnico: str
    nome: str
    descricao: str | None
    status: str
    dataConferencia: date


def _repo_buscar_tarefa(db: Session, tarefa_id: int) -> Tarefa | None:
    return db.get(Tarefa, tarefa_id)


def _repo_itens_da_tarefa(db: Session, tarefa_id: int) -> list[tuple[Item, ItensTarefa]]:
    consulta = (
        select(Item, ItensTarefa)
        .join(ItensTarefa, Item.id_itemTarefa == ItensTarefa.id)
        .where(ItensTarefa.id_tarefa == tarefa_id)
        .order_by(Item.id)
    )
    return list(db.execute(consulta).all())


def _repo_vinculo_do_item(db: Session, item_id: int) -> tuple[Item, ItensTarefa] | None:
    consulta = (
        select(Item, ItensTarefa)
        .join(ItensTarefa, Item.id_itemTarefa == ItensTarefa.id)
        .where(Item.id == item_id)
    )
    return db.execute(consulta).first()


def _repo_contar_itens(db: Session, tarefa_id: int, status: str | None = None) -> int:
    consulta = (
        select(func.count(Item.id))
        .join(ItensTarefa, Item.id_itemTarefa == ItensTarefa.id)
        .where(ItensTarefa.id_tarefa == tarefa_id)
    )
    if status is not None:
        consulta = consulta.where(ItensTarefa.statusItemTarefa == status)
    return db.scalar(consulta) or 0


def _repo_salvar(db: Session, obj) -> None:
    db.add(obj)
    db.commit()


def _repo_adicionar_item(db: Session, item: Item, vinculo: ItensTarefa) -> ItensTarefa:
    db.add(vinculo)
    db.flush()
    item.id_itemTarefa = vinculo.id
    db.commit()
    db.refresh(vinculo)
    return vinculo


def _repo_remover_item(db: Session, item: Item, vinculo: ItensTarefa) -> None:
    item.id_itemTarefa = None
    db.flush()
    restantes = db.scalar(select(Item.id).where(Item.id_itemTarefa == vinculo.id).limit(1))
    if restantes is None:
        db.delete(vinculo)
    db.commit()


def _svc__tarefa(db: Session, tarefa_id: int) -> Tarefa:
    tarefa = _repo_buscar_tarefa(db, tarefa_id)
    if tarefa is None:
        raise NaoEncontrado("Tarefa não encontrada")
    return tarefa


def _svc__vinculo(db: Session, tarefa_id: int, item_id: int) -> tuple[Item, ItensTarefa]:
    item = itens._repo_buscar(db, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    par = _repo_vinculo_do_item(db, item_id)
    if par is None or par[1].id_tarefa != tarefa_id:
        raise NaoEncontrado("Item não pertence a esta tarefa")
    return par


def _svc__saida(item: Item, vinculo: ItensTarefa) -> ItemTarefaSaida:
    return ItemTarefaSaida(
        id=item.id,
        codigoUnico=item.codigoUnico,
        nome=item.nome,
        descricao=item.descricao,
        status=vinculo.statusItemTarefa,
        dataConferencia=vinculo.dataConferencia,
    )


def _svc_iniciar(db: Session, tarefa_id: int) -> EstadoTarefa:
    tarefa = _svc__tarefa(db, tarefa_id)
    if tarefa.statusTarefas != "Pendante":
        raise Conflito("Somente tarefas pendentes podem ser iniciadas")
    tarefa.statusTarefas = "Em_Andamento"
    _repo_salvar(db, tarefa)
    return EstadoTarefa(mensagem="Tarefa iniciada", id=tarefa.id, status=tarefa.statusTarefas)


def _svc_concluir(db: Session, tarefa_id: int) -> EstadoTarefa:
    tarefa = _svc__tarefa(db, tarefa_id)
    if tarefa.statusTarefas != "Em_Andamento":
        raise Conflito("A tarefa precisa estar em andamento para ser concluída")
    total = _repo_contar_itens(db, tarefa_id)
    conferidos = _repo_contar_itens(db, tarefa_id, "Conferido")
    if total != conferidos:
        raise Conflito("Ainda existem itens pendentes de conferência")
    tarefa.statusTarefas = "Concluida"
    _repo_salvar(db, tarefa)
    return EstadoTarefa(mensagem="Tarefa concluída", id=tarefa.id, status=tarefa.statusTarefas)


def _svc_progresso(db: Session, tarefa_id: int) -> ProgressoTarefa:
    tarefa = _svc__tarefa(db, tarefa_id)
    total = _repo_contar_itens(db, tarefa_id)
    conferidos = _repo_contar_itens(db, tarefa_id, "Conferido")
    return ProgressoTarefa(
        tarefaId=tarefa_id,
        status=tarefa.statusTarefas,
        totalItens=total,
        itensConferidos=conferidos,
        itensPendentes=total - conferidos,
        percentual=round(conferidos * 100 / total, 2) if total else 0,
    )


def _svc_listar_itens(db: Session, tarefa_id: int) -> list[ItemTarefaSaida]:
    _svc__tarefa(db, tarefa_id)
    return [_svc__saida(item, vinculo) for item, vinculo in _repo_itens_da_tarefa(db, tarefa_id)]


def _svc_obter_item(db: Session, tarefa_id: int, item_id: int) -> ItemTarefaSaida:
    return _svc__saida(*_svc__vinculo(db, tarefa_id, item_id))


def _svc_adicionar_item(db: Session, tarefa_id: int, item_id: int) -> ItemTarefaSaida:
    tarefa = _svc__tarefa(db, tarefa_id)
    if tarefa.statusTarefas == "Concluida":
        raise Conflito("Tarefa concluída não pode receber itens")
    item = itens._repo_buscar(db, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    if item.id_itemTarefa is not None:
        raise Conflito("Item já associado a uma tarefa")
    vinculo = ItensTarefa(
        statusItemTarefa="Pendente",
        dataConferencia=date.today(),
        id_tarefa=tarefa_id,
    )
    try:
        vinculo = _repo_adicionar_item(db, item, vinculo)
    except IntegrityError as exc:
        db.rollback()
        raise Conflito("Não foi possível associar o item") from exc
    return _svc__saida(item, vinculo)


def _svc_remover_item(db: Session, tarefa_id: int, item_id: int) -> None:
    item, vinculo = _svc__vinculo(db, tarefa_id, item_id)
    _repo_remover_item(db, item, vinculo)


def _svc_conferir_item(db: Session, tarefa_id: int, item_id: int) -> ItemTarefaSaida:
    tarefa = _svc__tarefa(db, tarefa_id)
    if tarefa.statusTarefas != "Em_Andamento":
        raise Conflito("Inicie a tarefa antes de conferir itens")
    item, vinculo = _svc__vinculo(db, tarefa_id, item_id)
    if vinculo.statusItemTarefa == "Conferido":
        raise Conflito("Item já conferido")
    vinculo.statusItemTarefa = "Conferido"
    vinculo.dataConferencia = date.today()
    _repo_salvar(db, vinculo)
    return _svc__saida(item, vinculo)


router = APIRouter(prefix="/tarefas")

ERRO_404 = {404: {"model": Erro}, 503: {"model": Erro}}
ERRO_409 = {404: {"model": Erro}, 409: {"model": Erro}, 503: {"model": Erro}}


@router.post("/{id}/iniciar", tags=["Tarefas - Execução"], response_model=EstadoTarefa,
             responses=ERRO_409, summary="Iniciar tarefa")
def iniciar_tarefa(id: int, db: Session = Depends(get_db)):
    return _svc_iniciar(db, id)


@router.post("/{id}/concluir", tags=["Tarefas - Execução"], response_model=EstadoTarefa,
             responses=ERRO_409, summary="Concluir tarefa")
def concluir_tarefa(id: int, db: Session = Depends(get_db)):
    return _svc_concluir(db, id)


@router.get("/{id}/progresso", tags=["Tarefas - Execução"], response_model=ProgressoTarefa,
            responses=ERRO_404, summary="Consultar progresso da tarefa")
def progresso_tarefa(id: int, db: Session = Depends(get_db)):
    return _svc_progresso(db, id)


@router.get("/{id}/itens/all", tags=["Tarefas - Itens"],
            response_model=list[ItemTarefaSaida], responses=ERRO_404,
            summary="Listar itens da tarefa")
def listar_itens_tarefa(id: int, db: Session = Depends(get_db)):
    return _svc_listar_itens(db, id)


@router.get("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
            response_model=ItemTarefaSaida, responses=ERRO_404,
            summary="Consultar item da tarefa")
def obter_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    return _svc_obter_item(db, id, itemId)


@router.post("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
             response_model=ItemTarefaSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_409, summary="Adicionar item à tarefa")
def adicionar_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    return _svc_adicionar_item(db, id, itemId)


@router.delete("/{id}/itens/{itemId}", tags=["Tarefas - Itens"],
               status_code=status.HTTP_204_NO_CONTENT, responses=ERRO_404,
               summary="Remover item da tarefa")
def remover_item_tarefa(id: int, itemId: int, db: Session = Depends(get_db)):
    _svc_remover_item(db, id, itemId)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/itens/{itemId}/conferir", tags=["Tarefas - Itens"],
             response_model=ItemTarefaSaida, responses=ERRO_409,
             summary="Conferir item da tarefa")
def conferir_item(id: int, itemId: int, db: Session = Depends(get_db)):
    return _svc_conferir_item(db, id, itemId)
