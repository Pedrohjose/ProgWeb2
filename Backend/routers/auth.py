from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import update
from sqlalchemy import select
from sqlalchemy.orm import Session
from banco import get_db
from models import Usuario
from models.refresh_token import RefreshToken
from schemas import Login, LoginSaida, RefreshTokenEntrada, TokenAtualizado, respostas
from seguranca import (ACCESS_TOKEN_MINUTES, REFRESH_TOKEN_DAYS, criar_access_token,
                       get_current_user, hash_refresh_token, novo_refresh_token, verificar_senha)

router = APIRouter(tags=["Autenticação"])


@router.post("/login", response_model=LoginSaida, responses=respostas(401),
             summary="Validar email e senha",
             description="Valida as credenciais e retorna token de acesso Bearer (15 min) e refresh token rotativo (7 dias).")
def login(dados: Login, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not usuario.is_active or not verificar_senha(dados.senha, usuario.senha):
        raise HTTPException(401, "Email ou senha inválidos.")
    access, expires_in = criar_access_token(usuario)
    refresh = novo_refresh_token()
    db.add(RefreshToken(usuario_id=usuario.id, token_hash=hash_refresh_token(refresh),
                        family_id=str(uuid4()), expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)))
    db.commit()
    return {"mensagem": "Login realizado com sucesso", "usuario": usuario,
            "access_token": access, "refresh_token": refresh, "expires_in": expires_in}


@router.post("/refresh", response_model=TokenAtualizado, responses=respostas(401),
             summary="Renovar tokens", description="Rotaciona o refresh token de uso único e emite um novo token de acesso.")
def renovar_token(dados: RefreshTokenEntrada, db: Session = Depends(get_db)):
    token = dados.refresh_token
    registro = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token)))
    if registro is None:
        raise HTTPException(401, "Refresh token inválido.")
    if registro.revoked_at is not None:
        db.execute(update(RefreshToken).where(RefreshToken.family_id == registro.family_id,
                                              RefreshToken.revoked_at.is_(None)).values(revoked_at=datetime.utcnow()))
        db.commit()
        raise HTTPException(401, "Refresh token reutilizado. Sessão revogada.")
    agora = datetime.utcnow()
    if registro.expires_at <= agora:
        registro.revoked_at = agora
        db.commit()
        raise HTTPException(401, "Refresh token expirado.")
    usuario = db.get(Usuario, registro.usuario_id)
    if usuario is None or not usuario.is_active:
        registro.revoked_at = agora
        db.commit()
        raise HTTPException(401, "Usuário inválido ou inativo.")
    consumido = db.execute(update(RefreshToken).where(
        RefreshToken.id == registro.id, RefreshToken.revoked_at.is_(None)
    ).values(revoked_at=agora))
    if consumido.rowcount != 1:
        db.rollback()
        db.execute(update(RefreshToken).where(RefreshToken.family_id == registro.family_id,
                                              RefreshToken.revoked_at.is_(None)).values(revoked_at=agora))
        db.commit()
        raise HTTPException(401, "Refresh token reutilizado. Sessão revogada.")
    novo = novo_refresh_token()
    db.add(RefreshToken(usuario_id=usuario.id, token_hash=hash_refresh_token(novo),
                        family_id=registro.family_id, expires_at=agora + timedelta(days=REFRESH_TOKEN_DAYS)))
    access, expires_in = criar_access_token(usuario)
    db.commit()
    return {"access_token": access, "refresh_token": novo, "expires_in": expires_in}


@router.post("/logout", status_code=204, response_class=Response, summary="Encerrar sessão", description="Revoga o refresh token enviado.")
def logout(dados: RefreshTokenEntrada, db: Session = Depends(get_db)):
    registro = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(dados.refresh_token)))
    if registro and registro.revoked_at is None:
        registro.revoked_at = datetime.utcnow()
        db.commit()
    return Response(status_code=204)
