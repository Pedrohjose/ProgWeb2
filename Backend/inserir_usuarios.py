import os
import hashlib
import secrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from banco import engine
    from models import Usuario
except ImportError:
    try:
        from banco import engine
        from usuario import Usuario
    except ImportError:
        print("❌ Não foi possível encontrar os arquivos 'banco' ou 'models'.")
        exit(1)

def hash_senha(senha: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"

def ajustar_usuario():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Busca o usuário Carlos que já está cadastrado no banco pelo e-mail
        usuario_existente = session.query(Usuario).filter(Usuario.email == "carlos@estok.com").first()

        if usuario_existente:
            print("🔄 Usuário encontrado. Atualizando a senha para o formato criptografado...")
            usuario_existente.senha = hash_senha("senha123")
            session.commit()
            print("🎉 Senha do usuário 'Carlos' criptografada no banco com sucesso!")
        else:
            print("✨ Usuário não encontrado. Criando um novo registro com as propriedades do modelo...")
            senha_criptografada = hash_senha("senha123")
            
            # Criamos o objeto de forma segura. 
            # O SQLAlchemy vai mapear internamente para o campo correto usando synonym se estiver configurado.
            novo_usuario = Usuario(
                nome="Carlos",
                email="carlos@estok.com",
                senha=senha_criptografada
            )
            
            # Define o perfil/role dinamicamente baseado nos atributos disponíveis na classe
            if hasattr(novo_usuario, 'perfil'):
                novo_usuario.perfil = "Admin"
            elif hasattr(novo_usuario, 'role'):
                novo_usuario.role = "Admin"

            session.add(novo_usuario)
            session.commit()
            print("🎉 Novo usuário 'Carlos' inserido com senha criptografada!")

    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao processar no banco: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    ajustar_usuario()
