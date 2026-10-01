"""Cria uma tarefa descartável para a Collection do Pedro em banco de teste."""

from datetime import date, timedelta
from uuid import uuid4

from models.tarefa import Tarefa
from pedro_api.db import SessionLocal, engine


if engine.url.get_backend_name() == "mysql" and engine.url.database == "estok":
    raise SystemExit("Configure DATABASE_URL para um banco de teste antes de criar a tarefa.")

with SessionLocal() as db:
    tarefa = Tarefa(
        tituto=f"Validacao Pedro {uuid4().hex[:8]}",
        descricao="Tarefa temporária da Collection Postman",
        prazo=date.today() + timedelta(days=7),
        statusTarefas="Pendante",
    )
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    print(f"taskId={tarefa.id}")
