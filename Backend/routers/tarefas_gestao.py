from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from banco import get_db
from models import ItensTarefa, Tarefa, Usuario
from schemas import TarefaAtualizacao, TarefaEntrada, TarefaSaida, respostas
from permissoes_tarefas import tarefa_autorizada
from seguranca import exigir_roles, get_current_user, role_usuario

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
    if not usuario.is_active or role_usuario(usuario) != "Funcionario":
        raise HTTPException(422, "O responsável deve ser um Funcionario ativo.")
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
            description="Admin e Super Admin consultam todas as tarefas; Funcionario consulta somente as atribuídas a ele. Retorna [] se não houver tarefas.")
def listar_tarefas(db: Session = Depends(get_db), atual=Depends(get_current_user)):
    consulta = select(Tarefa).order_by(Tarefa.id)
    if role_usuario(atual) not in {"Admin", "Super Admin"}:
        consulta = consulta.where(Tarefa.id_usuario == atual.id)
    return db.scalars(consulta).all()


@router.get("/{id}", response_model=TarefaSaida, responses=respostas(401, 403, 404), summary="Consultar tarefa por ID",
            description="Funcionario consulta somente tarefa atribuída a ele. Admin e Super Admin consultam qualquer tarefa. ID inexistente retorna 404.")
def consultar_tarefa(tarefa: Tarefa = Depends(tarefa_autorizada)):
    return tarefa


@router.post("", status_code=201, response_model=TarefaSaida, responses=respostas(401, 403, 404, 409), summary="Criar tarefa",
             description="Exige Admin ou Super Admin. Pode criar sem responsável ou atribuir a um Funcionario ativo. O status padrão é Pendante. Título repetido retorna 409; responsável inexistente retorna 404; perfil incompatível ou inativo retorna 422.")
def criar_tarefa(dados: TarefaEntrada, db: Session = Depends(get_db), _admin=Depends(exigir_roles("Admin"))):
    if dados.id_usuario is not None:
        buscar_usuario(db, dados.id_usuario)
    tarefa = Tarefa(tituto=dados.titulo, descricao=dados.descricao, prazo=dados.prazo,
                    statusTarefas=dados.status.value, id_usuario=dados.id_usuario)
    db.add(tarefa)
    return salvar(db, tarefa)


@router.put("/{id}", response_model=TarefaSaida, responses=respostas(401, 403, 404, 409), summary="Editar tarefa",
            description="Item 5 da lista. Substitui título, descrição, prazo e status; envie todos os campos. O responsável não muda aqui: use PUT /tarefas/{id}/atribuir/{usuarioId}. Retorna 404 se a tarefa não existir e 409 se o título já pertencer a outra tarefa.")
def atualizar_tarefa(id: int, dados: TarefaAtualizacao, db: Session = Depends(get_db), _admin=Depends(exigir_roles("Admin"))):
    tarefa = buscar_tarefa(db, id)
    tarefa.tituto, tarefa.descricao, tarefa.prazo = dados.titulo, dados.descricao, dados.prazo
    tarefa.statusTarefas = dados.status.value
    return salvar(db, tarefa)


@router.delete("/{id}", status_code=204, response_class=Response, responses=respostas(401, 403, 404, 409), summary="Excluir tarefa",
               description="Item 6 da lista. Exclui definitivamente a tarefa e retorna 204 sem conteúdo. ID inexistente retorna 404. Tarefa com itens de conferência vinculados retorna 409, pois a cascata do modelo apagaria também os itens do patrimônio.")
def excluir_tarefa(id: int, db: Session = Depends(get_db), _admin=Depends(exigir_roles("Admin"))):
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


@router.put("/{id}/atribuir/{usuarioId}", response_model=TarefaSaida, responses=respostas(401, 403, 404),
            summary="Atribuir tarefa a um funcionário",
            description="Exige Admin ou Super Admin. Define um Funcionario ativo como responsável, substituindo o anterior. Tarefa ou usuário inexistente retorna 404; perfil incompatível ou inativo retorna 422.")
def atribuir_tarefa(id: int, usuarioId: int, db: Session = Depends(get_db), _admin=Depends(exigir_roles("Admin"))):
    tarefa = buscar_tarefa(db, id)
    usuario = buscar_usuario(db, usuarioId)
    tarefa.id_usuario = usuario.id
    return salvar(db, tarefa)
