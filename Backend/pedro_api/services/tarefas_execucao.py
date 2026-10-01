from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pedro_api.erros import Conflito, NaoEncontrado
from models.item import Item
from models.item_tarefa import ItensTarefa
from models.tarefa import Tarefa
from pedro_api.repositories import itens as repo_itens
from pedro_api.repositories import tarefas as repo_tarefas
from pedro_api.schemas import EstadoTarefa, ItemTarefaSaida, ProgressoTarefa


def _tarefa(db: Session, tarefa_id: int) -> Tarefa:
    tarefa = repo_tarefas.buscar_tarefa(db, tarefa_id)
    if tarefa is None:
        raise NaoEncontrado("Tarefa não encontrada")
    return tarefa


def _vinculo(db: Session, tarefa_id: int, item_id: int) -> tuple[Item, ItensTarefa]:
    item = repo_itens.buscar(db, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    par = repo_tarefas.vinculo_do_item(db, item_id)
    if par is None or par[1].id_tarefa != tarefa_id:
        raise NaoEncontrado("Item não pertence a esta tarefa")
    return par


def _saida(item: Item, vinculo: ItensTarefa) -> ItemTarefaSaida:
    return ItemTarefaSaida(
        id=item.id,
        codigoUnico=item.codigoUnico,
        nome=item.nome,
        descricao=item.descricao,
        status=vinculo.statusItemTarefa,
        dataConferencia=vinculo.dataConferencia,
    )


def iniciar(db: Session, tarefa_id: int) -> EstadoTarefa:
    tarefa = _tarefa(db, tarefa_id)
    if tarefa.statusTarefas != "Pendante":
        raise Conflito("Somente tarefas pendentes podem ser iniciadas")
    tarefa.statusTarefas = "Em_Andamento"
    repo_tarefas.salvar(db, tarefa)
    return EstadoTarefa(mensagem="Tarefa iniciada", id=tarefa.id, status=tarefa.statusTarefas)


def concluir(db: Session, tarefa_id: int) -> EstadoTarefa:
    tarefa = _tarefa(db, tarefa_id)
    if tarefa.statusTarefas != "Em_Andamento":
        raise Conflito("A tarefa precisa estar em andamento para ser concluída")
    total = repo_tarefas.contar_itens(db, tarefa_id)
    conferidos = repo_tarefas.contar_itens(db, tarefa_id, "Conferido")
    if total != conferidos:
        raise Conflito("Ainda existem itens pendentes de conferência")
    tarefa.statusTarefas = "Concluida"
    repo_tarefas.salvar(db, tarefa)
    return EstadoTarefa(mensagem="Tarefa concluída", id=tarefa.id, status=tarefa.statusTarefas)


def progresso(db: Session, tarefa_id: int) -> ProgressoTarefa:
    tarefa = _tarefa(db, tarefa_id)
    total = repo_tarefas.contar_itens(db, tarefa_id)
    conferidos = repo_tarefas.contar_itens(db, tarefa_id, "Conferido")
    return ProgressoTarefa(
        tarefaId=tarefa_id,
        status=tarefa.statusTarefas,
        totalItens=total,
        itensConferidos=conferidos,
        itensPendentes=total - conferidos,
        percentual=round(conferidos * 100 / total, 2) if total else 0,
    )


def listar_itens(db: Session, tarefa_id: int) -> list[ItemTarefaSaida]:
    _tarefa(db, tarefa_id)
    return [_saida(item, vinculo) for item, vinculo in repo_tarefas.itens_da_tarefa(db, tarefa_id)]


def obter_item(db: Session, tarefa_id: int, item_id: int) -> ItemTarefaSaida:
    return _saida(*_vinculo(db, tarefa_id, item_id))


def adicionar_item(db: Session, tarefa_id: int, item_id: int) -> ItemTarefaSaida:
    tarefa = _tarefa(db, tarefa_id)
    if tarefa.statusTarefas == "Concluida":
        raise Conflito("Tarefa concluída não pode receber itens")
    item = repo_itens.buscar(db, item_id)
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
        vinculo = repo_tarefas.adicionar_item(db, item, vinculo)
    except IntegrityError as exc:
        db.rollback()
        raise Conflito("Não foi possível associar o item") from exc
    return _saida(item, vinculo)


def remover_item(db: Session, tarefa_id: int, item_id: int) -> None:
    item, vinculo = _vinculo(db, tarefa_id, item_id)
    repo_tarefas.remover_item(db, item, vinculo)


def conferir_item(db: Session, tarefa_id: int, item_id: int) -> ItemTarefaSaida:
    tarefa = _tarefa(db, tarefa_id)
    if tarefa.statusTarefas != "Em_Andamento":
        raise Conflito("Inicie a tarefa antes de conferir itens")
    item, vinculo = _vinculo(db, tarefa_id, item_id)
    if vinculo.statusItemTarefa == "Conferido":
        raise Conflito("Item já conferido")
    vinculo.statusItemTarefa = "Conferido"
    vinculo.dataConferencia = date.today()
    repo_tarefas.salvar(db, vinculo)
    return _saida(item, vinculo)
