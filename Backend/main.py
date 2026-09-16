from fastapi import FastAPI, HTTPException
from usuario import Usuario, usuario_router
from pydantic import BaseModel

app = FastAPI()
app.include_router(usuario_router)
# Incluir Demais API's

class Login(BaseModel):
    email: str
    senha: str

@app.post("/login")
def logar(dados: Login):

    #Procurar o login no banco
    print(dados.email)
    print(dados.senha)

    if dados.email == "carlos@estok.com" and dados.senha == "senha":
        return {
            "mensagem": "Login realizado com sucesso",
            "usuario": {
                "id": 1,
                "nome": "Carlao",
                "email": "carlosestok.com",
                "perfil": "Admin Global"
            }
        }

    raise HTTPException(
        status_code=401,
        detail="Email ou senha inválidos"
    )

usuario = Usuario("Carlos", "carlos@gmail.com", "123", "Global")
usuario.adicinarUsuario()