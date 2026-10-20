"""Provisionamento local da primeira conta administrativa, sem endpoint público."""
import argparse
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from banco import SessionLocal
from models import Usuario
from schemas import UsuarioEntrada
from seguranca import hash_senha


def criar_primeiro_admin(db: Session, dados: UsuarioEntrada) -> Usuario:
    roles = {"Admin": "admin", "Super Admin": "super_admin"}
    if dados.perfil.value not in roles:
        raise ValueError("O provisionamento inicial exige Admin ou Super Admin.")
    existente = db.scalar(select(Usuario.id).where(func.lower(Usuario.role).in_(
        ("admin", "administrador", "super_admin", "super admin")
    )).limit(1))
    if existente is not None:
        raise ValueError("Já existe uma conta administrativa. Cadastre usuários pela API autenticada.")
    if db.scalar(select(Usuario.id).where(Usuario.email == dados.email)) is not None:
        raise ValueError("Email já cadastrado. Use outro email para a primeira conta administrativa.")
    usuario = Usuario(nome=dados.nome, email=dados.email, senha=hash_senha(dados.senha),
                      role=roles[dados.perfil.value], is_active=True)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--perfil", choices=("Admin", "Super Admin"), default="Admin")
    args = parser.parse_args()
    senha = getpass("Senha da primeira conta administrativa: ")
    if senha != getpass("Confirme a senha: "):
        parser.error("As senhas não coincidem.")
    try:
        dados = UsuarioEntrada(nome=args.nome, email=args.email, senha=senha, perfil=args.perfil)
    except ValidationError:
        parser.error("Verifique nome, email e senha (8 a 128 caracteres).")
    try:
        with SessionLocal() as db:
            usuario = criar_primeiro_admin(db, dados)
            print(f"Conta {args.perfil} criada: {usuario.email}. Faça login para cadastrar usuários.")
    except ValueError as exc:
        parser.error(str(exc))
    except SQLAlchemyError:
        parser.exit(1, "Falha ao provisionar a conta. Confira DB_* e as migrations do banco.\n")


if __name__ == "__main__":
    main()
