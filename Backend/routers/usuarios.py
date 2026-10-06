from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from banco import get_db
from models import Tarefa, Usuario
from schemas import SENHA_HASH, TarefaSaida, UsuarioEntrada, UsuarioSaida, respostas
from seguranca import hash_senha

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def buscar_usuario(db: Session, id: int) -> Usuario:
    usuario = db.get(Usuario, id)
    if usuario is None:
        raise HTTPException(404, "Usuário não encontrado.")
    return usuario


# Rotas com segmento fixo (/all) são registradas antes de /{id}.
@router.get("/all", response_model=list[UsuarioSaida], responses=respostas(), summary="Listar usuários",
            description="Item 8 da lista, originalmente escrito /usuarios/{all}. A palavra all é fixa nesta implementação. Retorna os usuários por ID crescente, sem senhas; retorna [] se não houver cadastros.")
def listar_usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.id)).all()


@router.get("/{id}/tarefas/all", response_model=list[TarefaSaida], responses=respostas(404),
            summary="Listar tarefas de um usuário",
            description="Item 13 da lista, originalmente escrito /usuarios/{id}/tarefas/{all}. Retorna as tarefas atribuídas ao usuário por ID crescente; [] se não houver nenhuma. Usuário inexistente retorna 404.")
def listar_tarefas_do_usuario(id: int, db: Session = Depends(get_db)):
    buscar_usuario(db, id)
    return db.scalars(select(Tarefa).where(Tarefa.id_usuario == id).order_by(Tarefa.id)).all()


@router.get("/{id}", response_model=UsuarioSaida, responses=respostas(404), summary="Consultar usuário por ID",
            description="Item 9 da lista. Retorna os dados públicos do usuário. ID inexistente retorna 404; ID não inteiro retorna 422.")
def consultar_usuario(id: int, db: Session = Depends(get_db)):
    return buscar_usuario(db, id)


@router.post("", status_code=201, response_model=UsuarioSaida, responses=respostas(409), summary="Cadastrar usuário",
             description=f"Item 10 da lista. Persiste o cadastro e retorna 201 com o ID. Email duplicado retorna 409. {SENHA_HASH}")
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


@router.put("/{id}", response_model=UsuarioSaida, responses=respostas(404, 409), summary="Atualizar usuário",
            description="Item 11 da lista. Substitui nome, email, senha e perfil do usuário indicado. Envie todos os campos. Retorna 404 se o ID não existir e 409 em caso de conflito de email.")
def atualizar_usuario(id: int, dados: UsuarioEntrada, db: Session = Depends(get_db)):
    usuario = buscar_usuario(db, id)
    usuario.nome, usuario.email = dados.nome, dados.email
    usuario.senha, usuario.perfil = hash_senha(dados.senha), dados.perfil.value
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email já cadastrado ou dados em conflito.")
    db.refresh(usuario)
    return usuario


@router.delete("/{id}", status_code=204, response_class=Response, responses=respostas(404, 409), summary="Excluir usuário",
               description="Item 12 da lista. Exclui definitivamente o usuário e retorna 204 sem conteúdo. ID inexistente retorna 404. Usuário com tarefas vinculadas retorna 409; essas tarefas precisam ser tratadas antes da exclusão.")
def excluir_usuario(id: int, db: Session = Depends(get_db)):
    usuario = buscar_usuario(db, id)
    if db.scalar(select(Tarefa.id).where(Tarefa.id_usuario == id).limit(1)) is not None:
        raise HTTPException(409, "Usuário possui tarefas vinculadas e não pode ser excluído.")
    db.delete(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Usuário possui vínculos que impedem a exclusão.")
    return Response(status_code=204)
