from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from banco import get_db
from models import ItensTarefa, Tarefa, Usuario
from schemas import TarefaAtualizacao, TarefaEntrada, TarefaSaida, respostas

router = APIRouter(prefix="/tarefas", tags=["Tarefas - Gestão"])
TITULO_DUPLICADO = "Já existe uma tarefa com este título."


def buscar_tarefa(db: Session, id: int) -> Tarefa:
    tarefa = db.get(Tarefa, id)
    if tarefa is None:
        raise HTTPException(404, "Tarefa não encontrada.")
    return tarefa


def buscar_usuario(db: Session, id: int) -> Usuario:
    usuario = db.get(Usuario, id)
    if usuario is None:
        raise HTTPException(404, "Usuário não encontrado.")
    return usuario


def salvar(db: Session, tarefa: Tarefa) -> Tarefa:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, TITULO_DUPLICADO)
    db.refresh(tarefa)
    return tarefa


# /all é registrado antes de /{id}: all é um segmento fixo, não um parâmetro.
@router.get("/all", response_model=list[TarefaSaida], responses=respostas(), summary="Listar tarefas",
            description="Item 2 da lista, originalmente escrito /tarefas/{all}. A palavra all é fixa nesta implementação. Retorna todas as tarefas por ID crescente; [] se não houver nenhuma.")
def listar_tarefas(db: Session = Depends(get_db)):
    return db.scalars(select(Tarefa).order_by(Tarefa.id)).all()


@router.get("/{id}", response_model=TarefaSaida, responses=respostas(404), summary="Consultar tarefa por ID",
            description="Item 3 da lista. ID inexistente retorna 404; ID não inteiro retorna 422.")
def consultar_tarefa(id: int, db: Session = Depends(get_db)):
    return buscar_tarefa(db, id)


@router.post("", status_code=201, response_model=TarefaSaida, responses=respostas(404, 409), summary="Criar tarefa",
             description="Item 4 da lista. Retorna 201 com a tarefa criada. O status padrão é Pendante. Título repetido retorna 409; `id_usuario` informado e inexistente retorna 404.")
def criar_tarefa(dados: TarefaEntrada, db: Session = Depends(get_db)):
    if dados.id_usuario is not None:
        buscar_usuario(db, dados.id_usuario)
    tarefa = Tarefa(tituto=dados.titulo, descricao=dados.descricao, prazo=dados.prazo,
                    statusTarefas=dados.status.value, id_usuario=dados.id_usuario)
    db.add(tarefa)
    return salvar(db, tarefa)


@router.put("/{id}", response_model=TarefaSaida, responses=respostas(404, 409), summary="Editar tarefa",
            description="Item 5 da lista. Substitui título, descrição, prazo e status; envie todos os campos. O responsável não muda aqui: use PUT /tarefas/{id}/atribuir/{usuarioId}. Retorna 404 se a tarefa não existir e 409 se o título já pertencer a outra tarefa.")
def atualizar_tarefa(id: int, dados: TarefaAtualizacao, db: Session = Depends(get_db)):
    tarefa = buscar_tarefa(db, id)
    tarefa.tituto, tarefa.descricao, tarefa.prazo = dados.titulo, dados.descricao, dados.prazo
    tarefa.statusTarefas = dados.status.value
    return salvar(db, tarefa)


@router.delete("/{id}", status_code=204, response_class=Response, responses=respostas(404, 409), summary="Excluir tarefa",
               description="Item 6 da lista. Exclui definitivamente a tarefa e retorna 204 sem conteúdo. ID inexistente retorna 404. Tarefa com itens de conferência vinculados retorna 409, pois a cascata do modelo apagaria também os itens do patrimônio.")
def excluir_tarefa(id: int, db: Session = Depends(get_db)):
    tarefa = buscar_tarefa(db, id)
    if db.scalar(select(ItensTarefa.id).where(ItensTarefa.id_tarefa == id).limit(1)) is not None:
        raise HTTPException(409, "Tarefa possui itens de conferência vinculados e não pode ser excluída.")
    db.delete(tarefa)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Tarefa possui vínculos que impedem a exclusão.")
    return Response(status_code=204)


@router.put("/{id}/atribuir/{usuarioId}", response_model=TarefaSaida, responses=respostas(404),
            summary="Atribuir tarefa a um usuário",
            description="Item 7 da lista. Define o usuário responsável pela tarefa (substitui o anterior, se houver) e retorna a tarefa atualizada. Tarefa ou usuário inexistente retorna 404.")
def atribuir_tarefa(id: int, usuarioId: int, db: Session = Depends(get_db)):
    tarefa = buscar_tarefa(db, id)
    usuario = buscar_usuario(db, usuarioId)
    tarefa.id_usuario = usuario.id
    return salvar(db, tarefa)
