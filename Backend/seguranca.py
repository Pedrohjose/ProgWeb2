import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from banco import get_db
from models import Usuario

ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
JWT_ALGORITHM = "HS256"
# A chave local facilita a execução acadêmica. Produção deve sempre configurar uma chave aleatória.
JWT_SECRET = os.getenv("AUTH_SECRET_KEY", "estok-development-only-change-this-secret-key")
if os.getenv("APP_ENV", "development").lower() == "production" and len(JWT_SECRET) < 32:
    raise RuntimeError("Configure AUTH_SECRET_KEY com pelo menos 32 caracteres em produção.")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_senha(senha):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verificar_senha(senha, valor):
    try:
        algoritmo, vezes, salt, esperado = valor.split("$")
        if algoritmo != "pbkdf2_sha256" or int(vezes) != 600000:
            return False
        obtido = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), int(vezes)).hex()
        return hmac.compare_digest(obtido, esperado)
    except (ValueError, AttributeError):
        return False


def role_usuario(usuario: Usuario) -> str:
    role = str(usuario.role or "usuario").lower()
    if role in {"super_admin", "super admin"}:
        return "Super Admin"
    if role in {"admin", "administrador"}:
        return "Admin"
    return "Funcionario"


def criar_access_token(usuario: Usuario) -> tuple[str, int]:
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    token = jwt.encode({"sub": str(usuario.id), "role": role_usuario(usuario), "type": "access",
                        "jti": str(uuid4()), "exp": expira_em}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_MINUTES * 60


def novo_refresh_token():
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decodificar_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access" or not payload.get("sub"):
            raise jwt.InvalidTokenError("Tipo de token inválido")
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.",
                            headers={"WWW-Authenticate": "Bearer"})


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
                     db: Session = Depends(get_db)) -> Usuario:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Autenticação Bearer obrigatória.", headers={"WWW-Authenticate": "Bearer"})
    payload = decodificar_access_token(credentials.credentials)
    try:
        usuario_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(401, "Token inválido.", headers={"WWW-Authenticate": "Bearer"})
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.is_active:
        raise HTTPException(401, "Usuário inválido ou inativo.", headers={"WWW-Authenticate": "Bearer"})
    return usuario


def exigir_roles(*roles):
    def verificar(usuario: Usuario = Depends(get_current_user)):
        role = role_usuario(usuario)
        if role not in roles and not (role == "Super Admin" and "Admin" in roles):
            raise HTTPException(403, "Você não tem permissão para esta operação.")
        return usuario
    return verificar
