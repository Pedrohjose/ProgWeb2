"""Permissões compartilhadas entre consulta e execução de tarefas."""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from banco import get_db
from models import Tarefa, Usuario
from seguranca import get_current_user, role_usuario


def tarefa_autorizada(id: int, db: Session = Depends(get_db),
                      atual: Usuario = Depends(get_current_user)) -> Tarefa:
    tarefa = db.get(Tarefa, id)
    if tarefa is None:
        raise HTTPException(404, "Tarefa não encontrada.")
    if role_usuario(atual) not in {"Admin", "Super Admin"} and tarefa.id_usuario != atual.id:
        raise HTTPException(403, "Você só pode acessar tarefas atribuídas a você.")
    return tarefa
