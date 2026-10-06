# ESTOK — API REST e Swagger de Testes

Base do sistema de gerenciamento de patrimônio ESTOK, desenvolvida com FastAPI, SQLAlchemy, Alembic e MySQL.

**Versão 0.2.0:** seis endpoints funcionais do escopo original, com documentação Swagger, exemplos e Collection do Postman. As rotas de diagnóstico são adicionais. A base está preparada para o grupo continuar a implementação.

## Endpoints implementados

| Item da lista original | Método | Rota | Resposta de sucesso |
|---|---|---|---|
| 1 | POST | `/login` | 200 — credenciais válidas e usuário |
| 8 | GET | `/usuarios/all` | 200 — lista de usuários |
| 9 | GET | `/usuarios/{id}` | 200 — usuário encontrado |
| 10 | POST | `/usuarios` | 201 — usuário criado |
| 11 | PUT | `/usuarios/{id}` | 200 — usuário atualizado |
| 12 | DELETE | `/usuarios/{id}` | 204 — excluído, sem corpo |

Na lista original, o item 8 aparece como `/usuarios/{all}`. Aqui usamos `/usuarios/all`: `all` é um texto fixo para listar todos, enquanto `{id}` representa um identificador variável. A rota GET `/usuarios/all` é registrada antes de GET `/usuarios/{id}`.

**Auxiliares:** `GET /saude` verifica a API; `GET /saude/banco` verifica a conexão.

## Iniciar no Windows

Requisitos: Python 3.13, MySQL Server 8.0 e a senha do usuário root local.

No PowerShell **como administrador**, inicie o banco:

```powershell
Start-Service MySQL80
```

Em outro PowerShell, **normal**, na raiz do repositório:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Backend\iniciar.ps1
```

O script prepara `.venv`, instala as dependências, pede a senha do root local, prepara `estok_joao`, aplica as migrations pendentes e inicia a API na porta 8000. A senha é usada somente durante a execução; não é salva no código. Bypass vale apenas para esse processo do PowerShell.

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI: http://127.0.0.1:8000/openapi.json

Esses endereços são locais. O professor precisa executar o projeto no computador dele para acessá-los por `127.0.0.1`.

## Testar no Swagger

Em cada rota, clique em **Try it out → Execute** e confira o **Server response**, que é a resposta real. Exemplos na documentação não são resultados de testes.

1. Execute `GET /saude/banco`: espere 200.
2. Cadastre um usuário com o JSON abaixo em `POST /usuarios`: espere 201 e guarde o `id` retornado.
3. Execute `POST /login` com o mesmo email e senha: espere 200. Senha incorreta retorna 401.
4. Execute `GET /usuarios/all` e `GET /usuarios/{id}`: espere 200 e os dados cadastrados, sem senha.
5. Execute `PUT /usuarios/{id}` com todos os campos, alterando o nome. Consulte novamente para conferir a persistência.
6. Exclua somente o usuário de teste com `DELETE /usuarios/{id}`: espere 204 sem conteúdo. Consultar o ID excluído retorna 404.

```json
{
  "nome": "Usuário de Teste",
  "email": "teste@example.com",
  "senha": "TesteLocal123!",
  "perfil": "Funcionario"
}
```

Para repetir o cadastro sem excluir antes, use outro email. Email duplicado retorna 409. Os perfis aceitos são `Admin` e `Funcionario`; a senha da aplicação precisa de 8 a 128 caracteres. Essa senha não é a senha do MySQL.

## Erros documentados

| Código | Situação |
|---|---|
| 401 | Email ou senha inválidos no login |
| 404 | Usuário inexistente em consulta, atualização ou exclusão |
| 409 | Email duplicado ou vínculos que impedem exclusão |
| 422 | Campos inválidos ou ID não inteiro |
| 503 | Banco indisponível ou schema incompatível |

Usuário com tarefas vinculadas não pode ser excluído (409). Isso evita que a exclusão leve consigo tarefas pela configuração de cascata do modelo. Login ainda não emite token, e as rotas não exigem autenticação/autorização nesta etapa acadêmica; a política final deve ser implementada pelo grupo.

## Postman

Importe `ESTOK.postman_collection.json` e abra o Collection Runner. Mantenha `base_url` como `http://127.0.0.1:8000` e execute as **16 requisições na ordem**.

O fluxo gera um email exclusivo, salva o ID criado, testa os seis endpoints e exclui o usuário de teste ao final. Verifica códigos HTTP, leitura, atualização e ausência de senha nas respostas. Se a execução for interrompida, o usuário de teste pode permanecer no banco. Não confundir 16 casos de teste com 16 endpoints: há seis endpoints do escopo.

## Migrations e compatibilidade

A atualização 0.2.0 não altera tabelas, modelos, senha do MySQL nem o histórico `joao_baseline_01`. Continua usando o banco de desenvolvimento `estok_joao`, para preservar os dados da base anterior. Não execute `CriacaoBanco.sql` junto com a migration nem aponte essa baseline para um banco de outra origem.

## Pendências da lista de 20

Permanecem **14 endpoints**: gestão de tarefas (itens 2–7), consulta de tarefas por usuário (item 13) e localizações (itens 14–20). Não estão declarados como implementados nem simulados no Swagger. O grupo pode adicionar rotas e schemas; o FastAPI atualizará a documentação correspondente.

## Validação da versão

Testes automatizados executados com Python 3.12 e SQLite isolado: documentação, seis operações, persistência, respostas 401/404/409/422/503, ausência de senha nas respostas, exclusão sem corpo e preservação de tarefas vinculadas. Também foi reproduzida a sequência de 16 requisições da Collection com o cliente de testes; os scripts JavaScript não foram executados no aplicativo Postman.

A versão anterior foi executada por João com MySQL no Windows. Esta atualização ainda precisa do teste final nesse ambiente; não foi alegada validação nova em MySQL ou PowerShell.

Para repetir os testes na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\Backend\requirements-dev.txt
cd Backend
..\.venv\Scripts\python.exe -m unittest -v test_api
```

## Parar

No terminal da API, pressione **Ctrl+C**. Para parar o banco, use PowerShell como administrador:

```powershell
Stop-Service MySQL80
Set-Service MySQL80 -StartupType Manual
```

## Commit após testar

Confira se está na branch desejada e se não existem alterações de colegas para integrar. Na raiz:

```powershell
git status --short
git add Backend/main.py Backend/test_api.py Backend/ESTOK.postman_collection.json Backend/README.md Backend/LEIA-ME.md README.md
git commit -m "Amplia API para seis endpoints e atualiza Swagger e testes do ESTOK"
git push origin joao
```

Não inclua `.venv`, senhas ou ZIPs de entrega no commit. O push acima deve ser usado somente quando a branch atual for `joao`.
