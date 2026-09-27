from fastapi import FastAPI, HTTPException
from usuario import Usuario, usuario_router
from pydantic import BaseModel
from banco import conectar

app = FastAPI()
app.include_router(usuario_router)

class Login(BaseModel):
    email: str
    senha: str

@app.post("/login")
def logar(dados: Login):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    sql = """
        SELECT id, nome, email, senha, perfil
        FROM usuarios
        WHERE email = %s AND senha = %s"""

    cursor.execute(sql, (dados.email, dados.senha))

    usuario = cursor.fetchone()

    cursor.close()
    conexao.close()

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha inválidos"
        )

    return {
        "messagem": "Login realizado com sucesso",
        "usuario": usuario
    } 
