from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from banco import get_db
from models import Usuario
from schemas import Login, LoginSaida, respostas
from seguranca import verificar_senha

router = APIRouter(tags=["Autenticação"])


@router.post("/login", response_model=LoginSaida, responses=respostas(401),
             summary="Validar email e senha",
             description="Item 1 da lista. Retorna 200 e os dados públicos do usuário ou 401 se as credenciais forem inválidas. Não gera token nesta etapa.")
def login(dados: Login, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha):
        raise HTTPException(401, "Email ou senha inválidos.")
    return {"mensagem": "Login realizado com sucesso", "usuario": usuario}
