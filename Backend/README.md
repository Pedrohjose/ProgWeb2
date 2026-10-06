# ESTOK — API REST e Swagger de Testes

Base do sistema de gerenciamento de patrimônio ESTOK, desenvolvida com FastAPI, SQLAlchemy, Alembic e MySQL.

**Versão 0.3.0:** os 20 endpoints do escopo (login, usuários, localizações e gestão de tarefas), com documentação Swagger, exemplos e Collection do Postman. As rotas de diagnóstico são adicionais.

## Estrutura do código

```text
Backend/
├── main.py                  # cria o app, Swagger, tratamento de erro de banco e inclui os routers
├── schemas.py               # schemas Pydantic (entrada, saída, erros)
├── routers/
│   ├── auth.py              # Login
│   ├── usuarios.py          # Usuários (+ tarefas do usuário)
│   ├── localizacoes.py      # Localizações (+ itens e QR Codes)
│   └── tarefas_gestao.py    # Gestão de tarefas
└── models/                  # modelos SQLAlchemy (inalterados)
```

## Endpoints implementados

| Item | Método | Rota | Sucesso | Erros documentados |
|---|---|---|---|---|
| 1 | POST | `/login` | 200 | 401, 422 |
| 2 | GET | `/tarefas/all` | 200 | — |
| 3 | GET | `/tarefas/{id}` | 200 | 404, 422 |
| 4 | POST | `/tarefas` | 201 | 404 (usuário), 409 (título), 422 |
| 5 | PUT | `/tarefas/{id}` | 200 | 404, 409 (título), 422 |
| 6 | DELETE | `/tarefas/{id}` | 204 | 404, 409 (itens vinculados) |
| 7 | PUT | `/tarefas/{id}/atribuir/{usuarioId}` | 200 | 404 (tarefa ou usuário) |
| 8 | GET | `/usuarios/all` | 200 | — |
| 9 | GET | `/usuarios/{id}` | 200 | 404, 422 |
| 10 | POST | `/usuarios` | 201 | 409 (email), 422 |
| 11 | PUT | `/usuarios/{id}` | 200 | 404, 409, 422 |
| 12 | DELETE | `/usuarios/{id}` | 204 | 404, 409 (tarefas vinculadas) |
| 13 | GET | `/usuarios/{id}/tarefas/all` | 200 | 404 |
| 14 | GET | `/localizacoes/all` | 200 | — |
| 15 | GET | `/localizacoes/{id}` | 200 | 404, 422 |
| 16 | POST | `/localizacoes` | 201 | 422 |
| 17 | PUT | `/localizacoes/{id}` | 200 | 404, 422 |
| 18 | DELETE | `/localizacoes/{id}` | 204 | 404, 409 (itens vinculados) |
| 19 | GET | `/localizacoes/{id}/itens/all` | 200 | 404 |
| 20 | GET | `/localizacoes/{id}/qrcode/all` | 200 | 404 |

Na lista original, os itens 2, 8, 13, 14, 19 e 20 aparecem com `{all}`. Aqui usamos `all` como **texto fixo** (`/tarefas/all`), pois `{id}` é que representa um identificador variável. As rotas com `all` são registradas antes das rotas com `{id}`.

**Interpretações a confirmar com o grupo:**
- **Item 20** — `/localizacoes/{id}/qrcode/all` retorna, para cada item da localização, o QR Code do `codigoUnico` como imagem SVG em *data URI* (`item_id`, `codigoUnico`, `nome`, `qrcode`). Depende da biblioteca `segno`.
- **Campos de tarefa** — o banco tem as colunas `tituto` (sem o "l") e `statusTarefas`; a API expõe `titulo` e `status`. O status aceita os valores do enum do modelo: `Pendante`, `Em_Andamento` e `Concluida` ("Pendante" é grafia do modelo; corrigir exige alterar o enum e criar migration).
- **Atribuição** — `PUT /tarefas/{id}` não altera o responsável; isso é feito somente em `PUT /tarefas/{id}/atribuir/{usuarioId}`.
- **Exclusões** — tarefas com itens de conferência e localizações com itens retornam 409, porque a cascata dos modelos apagaria também os itens do patrimônio.

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

O script prepara `.venv`, instala as dependências, pede a senha do root local, prepara `estok`, aplica as migrations pendentes e inicia a API na porta 8000. A senha é usada somente durante a execução; não é salva no código. Bypass vale apenas para esse processo do PowerShell.

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI: http://127.0.0.1:8000/openapi.json

Esses endereços são locais. O professor precisa executar o projeto no computador dele para acessá-los por `127.0.0.1`.

## Testar no Swagger

Em cada rota, clique em **Try it out → Execute** e confira o **Server response**, que é a resposta real. Exemplos na documentação não são resultados de testes.

1. `GET /saude/banco`: espere 200.
2. `POST /usuarios` com o JSON abaixo: espere 201 e guarde o `id`. `POST /login` com o mesmo email e senha: 200 (senha incorreta: 401).
3. `POST /localizacoes` (o Swagger já traz um exemplo): 201. Consulte, liste, atualize e confira `itens/all` e `qrcode/all` (listas vazias numa localização nova).
4. `POST /tarefas` (o `id_usuario` é opcional): 201. Edite em `PUT /tarefas/{id}` e atribua em `PUT /tarefas/{id}/atribuir/{usuarioId}`. Confira em `GET /usuarios/{id}/tarefas/all`.
5. Exclua tarefa, localização e usuário de teste, nessa ordem: 204 sem conteúdo. Consultar de novo retorna 404.

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
| 404 | Usuário, tarefa ou localização inexistente |
| 409 | Email ou título de tarefa duplicado; exclusão bloqueada por vínculos |
| 422 | Campos inválidos (ex.: CEP fora de 8 dígitos, data inválida) ou ID não inteiro |
| 503 | Banco indisponível ou schema incompatível |

Usuário com tarefas, tarefa com itens de conferência e localização com itens não podem ser excluídos (409). Login ainda não emite token, e as rotas não exigem autenticação/autorização nesta etapa acadêmica; a política final deve ser implementada pelo grupo.

## Postman

Importe `ESTOK.postman_collection.json` (**ESTOK API**) e abra o Collection Runner. Mantenha `base_url` como `http://127.0.0.1:8000` e execute a collection inteira, **na ordem**. Pastas:

```text
ESTOK API
├── Diagnóstico         (2 requisições)
├── Autenticação        (6)
├── Usuários            (18)
├── Localizações        (14)
└── Tarefas - Gestão    (18)
```

Cada pasta cria os próprios dados de teste (emails e títulos únicos), salva os IDs em variáveis e exclui tudo ao final; por isso pode ser executada isoladamente. Cada requisição verifica o código HTTP e, quando aplicável, o conteúdo da resposta (sem senha, dados persistidos, responsável atribuído, etc.). Se a execução for interrompida, os dados de teste podem permanecer no banco. São 58 requisições de teste para 20 endpoints.

## Migrations e compatibilidade

As atualizações 0.2.0 e 0.3.0 não alteram tabelas, modelos, senha do MySQL nem o histórico `joao_baseline_01`. Continua usando o banco de desenvolvimento `estok`, para preservar os dados da base anterior. Não execute `CriacaoBanco.sql` junto com a migration nem aponte essa baseline para um banco de outra origem.

## Validação da versão

Executado neste ambiente com Python 3.12 e SQLite isolado: **16 testes automatizados passaram**, cobrindo os 20 endpoints (códigos 200/201/204/401/404/409/422/503), persistência, ausência de senha nas respostas, exclusão sem corpo, preservação de itens do patrimônio e geração de QR Code. O teste da Collection executa as 58 requisições contra a API e confere os códigos HTTP declarados e a cobertura dos 20 endpoints. As asserções JavaScript da Collection também foram executadas em Node, com um substituto do objeto `pm`, sem falhas.

**Não foi validado:** o aplicativo Postman em si, o PowerShell e o MySQL real. A versão 0.3.0 não altera modelos nem migrations, mas ainda precisa do teste final no MySQL do Windows.

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
git add Backend/main.py Backend/schemas.py Backend/routers Backend/requirements.txt Backend/test_api.py Backend/ESTOK.postman_collection.json Backend/README.md README.md
git commit -m "Implementa os 20 endpoints de login, usuários, localizações e tarefas"
git push origin joao
```

Não inclua `.venv`, senhas ou ZIPs de entrega no commit. O push acima deve ser usado somente quando a branch atual for `joao`.
