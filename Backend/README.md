# ESTOK — API REST e Swagger de Testes

Base do sistema de gerenciamento de patrimônio ESTOK, desenvolvida com FastAPI, SQLAlchemy, Alembic e MySQL.

**Versão 0.4.0:** API REST com JWT, refresh token rotativo e perfis Admin, Funcionario e Super Admin. As rotas de diagnóstico são adicionais.

## Estrutura do código

```text
Backend/
├── main.py                  # cria o app, Swagger, tratamento de erro de banco e inclui os routers
├── schemas.py               # schemas Pydantic (entrada, saída, erros)
├── routers/
│   ├── auth.py              # Login
│   ├── usuarios.py          # Usuários (+ tarefas do usuário)
│   ├── localizacoes.py      # Localizações (+ itens e QR Codes)
│   ├── tarefas_gestao.py    # Gestão e atribuição de tarefas
│   └── tarefas_execucao.py  # Execução pelo funcionário atribuído
├── criar_admin.py           # provisionamento local da primeira conta administrativa
├── permissoes_tarefas.py    # controle de acesso à tarefa pelo responsável
└── models/                  # modelos SQLAlchemy (inalterados)
```

## Endpoints implementados

| Item | Método | Rota | Sucesso | Erros documentados |
|---|---|---|---|---|
| 1 | POST | `/login` | 200 (tokens) | 401, 422 |
| — | POST | `/refresh` | 200 (tokens rotacionados) | 401, 422 |
| — | POST | `/logout` | 204 | 422 |
| 2 | GET | `/tarefas/all` | 200 | — |
| 3 | GET | `/tarefas/{id}` | 200 | 404, 422 |
| 4 | POST | `/tarefas` | 201 | 401, 403, 404 (usuário), 409 (título), 422 |
| 5 | PUT | `/tarefas/{id}` | 200 | 401, 403, 404, 409 (título), 422 |
| 6 | DELETE | `/tarefas/{id}` | 204 | 401, 403, 404, 409 (itens vinculados) |
| 7 | PUT | `/tarefas/{id}/atribuir/{usuarioId}` | 200 | 401, 403, 404 (tarefa ou usuário), 422 |
| 8 | GET | `/usuarios/all` | 200 | — |
| 9 | GET | `/usuarios/{id}` | 200 | 404, 422 |
| 10 | POST | `/usuarios` | 201 | 401, 403, 409 (email), 422 |
| 11 | PUT | `/usuarios/{id}` | 200 | 404, 409, 422 |
| 12 | DELETE | `/usuarios/{id}` | 204 | 404, 409 (tarefas vinculadas) |
| 13 | GET | `/usuarios/{id}/tarefas/all` | 200 | 404 |
| 14 | GET | `/localizacoes/all` | 200 | — |
| 15 | GET | `/localizacoes/{id}` | 200 | 404, 422 |
| 16 | POST | `/localizacoes` | 201 | 401, 403, 422 |
| 17 | PUT | `/localizacoes/{id}` | 200 | 401, 403, 404, 422 |
| 18 | DELETE | `/localizacoes/{id}` | 204 | 401, 403, 404, 409 (itens vinculados) |
| 19 | GET | `/localizacoes/{id}/itens/all` | 200 | 404 |
| 20 | GET | `/localizacoes/{id}/qrcode/all` | 200 | 404 |

Na lista original, os itens 2, 8, 13, 14, 19 e 20 aparecem com `{all}`. Aqui usamos `all` como **texto fixo** (`/tarefas/all`), pois `{id}` é que representa um identificador variável. As rotas com `all` são registradas antes das rotas com `{id}`.

**Interpretações a confirmar com o grupo:**
- **Item 20** — `/localizacoes/{id}/qrcode/all` retorna, para cada item da localização, o QR Code do `codigoUnico` como imagem SVG em *data URI* (`item_id`, `codigoUnico`, `nome`, `qrcode`). Depende da biblioteca `segno`.
- **Campos de tarefa** — o banco tem as colunas `tituto` (sem o "l") e `statusTarefas`; a API expõe `titulo` e `status`. O status aceita os valores do enum do modelo: `Pendante`, `Em_Andamento` e `Concluida` ("Pendante" é grafia do modelo; corrigir exige alterar o enum e criar migration).
- **Atribuição** — somente Admin ou Super Admin pode criar, editar, excluir e atribuir tarefas. O responsável deve ser um Funcionario ativo. `PUT /tarefas/{id}` não altera o responsável; isso é feito em `PUT /tarefas/{id}/atribuir/{usuarioId}`.
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
2. Provisione a primeira conta administrativa pelo comando local abaixo. Faça `POST /login` com uma conta Admin ou Super Admin, copie `access_token` e cole somente esse token no botão **Authorize** do Swagger. Então execute `POST /usuarios` com o JSON abaixo: espere 201 e guarde o `id`. Sem token retorna 401; com perfil Funcionario retorna 403.
3. `POST /localizacoes` (o Swagger já traz um exemplo): 201. Consulte, liste, atualize e confira `itens/all` e `qrcode/all` (listas vazias numa localização nova).
4. Como Admin ou Super Admin, crie uma tarefa em `POST /tarefas` (`id_usuario` é opcional), edite em `PUT /tarefas/{id}` e atribua a um Funcionario ativo em `PUT /tarefas/{id}/atribuir/{usuarioId}`. Defina os itens da conferência. Entre com o funcionário atribuído para listar, iniciar, conferir e concluir a tarefa. Um funcionário não consegue consultar ou executar tarefas de outro.
5. Exclua tarefa, localização e usuário de teste, nessa ordem: 204 sem conteúdo. Consultar de novo retorna 404.

```json
{
  "nome": "Usuário de Teste",
  "email": "teste@example.com",
  "senha": "TesteLocal123!",
  "perfil": "Funcionario"
}
```

Para repetir o cadastro sem excluir antes, use outro email. Email duplicado retorna 409. Admin pode cadastrar ou atualizar usuários como `Admin` ou `Funcionario`; somente Super Admin pode conceder `Super Admin`. A senha da aplicação precisa de 8 a 128 caracteres. Essa senha não é a senha do MySQL.

## Erros documentados

| Código | Situação |
|---|---|
| 401 | Autenticação ausente, inválida ou expirada |
| 403 | Usuário autenticado sem permissão para a operação ou perfil solicitado |
| 404 | Usuário, tarefa ou localização inexistente |
| 409 | Email ou título de tarefa duplicado; exclusão bloqueada por vínculos |
| 422 | Campos inválidos (ex.: CEP fora de 8 dígitos, data inválida) ou ID não inteiro |
| 503 | Banco indisponível ou schema incompatível |

Usuário com tarefas, tarefa com itens de conferência e localização com itens não podem ser excluídos (409). Itens, QR Codes, localizações e tarefas exigem token Bearer. Gestão de usuários (cadastrar, listar, consultar, atualizar e excluir) exige Admin ou Super Admin; cada usuário pode consultar apenas suas tarefas, salvo Admin e Super Admin. Não há cadastro público. Somente Super Admin pode conceder esse perfil ou alterar/excluir uma conta Super Admin. Refresh tokens são aleatórios, guardados no banco somente como hash, expiram em 7 dias e são rotacionados em cada renovação. Access tokens JWT expiram em 15 minutos.

Admin e Super Admin cadastram, editam e excluem localizações; Funcionario consulta localizações, itens armazenados e QR Codes. A gestão de tarefas e a adição/remoção de seus itens também são administrativas. Funcionario lista, consulta, inicia, confere e conclui somente as tarefas atribuídas a ele. Uma reatribuição remove imediatamente o acesso do funcionário anterior, inclusive com token ainda válido.

### Perfis e permissões

| Perfil | Acesso |
|---|---|
| `Funcionario` | Consulta localizações e executa somente tarefas atribuídas a ele. Não cadastra usuários nem gerencia tarefas ou localizações. |
| `Admin` | Gerencia usuários, tarefas, seus itens e localizações. Atribui tarefas a funcionários ativos. Pode conceder perfil Admin, mas não Super Admin. |
| `Super Admin` | Herda o acesso de Admin e pode conceder o perfil Super Admin a outros usuários, além de alterar ou excluir contas Super Admin. |

Itens de patrimônio e QR Codes continuam exigindo autenticação. As restrições acima são aplicadas no backend; a interface web ainda não esconde telas ou ações por perfil.

### Autenticação e primeiro Admin

O access token deve ser enviado como `Authorization: Bearer <access_token>`. Renove a sessão enviando `POST /refresh` com `{"refresh_token":"..."}`; a resposta fornece um access token e um refresh token novos. Cada refresh token só pode ser usado uma vez. Reutilizar um token antigo revoga a família da sessão. `POST /logout` com o refresh token encerra a sessão.

Em um banco sem conta administrativa, com as migrations aplicadas, as dependências Python instaladas e as mesmas variáveis `DB_*` usadas pela API configuradas, execute na raiz do projeto:

```powershell
python .\Backend\criar_admin.py --nome "Admin Inicial" --email "admin@example.com" --perfil "Admin"
```

O comando pede a senha sem exibi-la e recusa criar contas se já existir Admin ou Super Admin. Para iniciar com Super Admin, use `--perfil "Super Admin"`. Depois, cadastre as demais contas pela API autenticada. As roles são armazenadas como `usuario`, `admin` ou `super_admin`; nenhuma alteração estrutural do banco é necessária, pois a coluna `role` já é textual.

Configure uma chave secreta persistente antes de iniciar o backend; a chave embutida é apenas para desenvolvimento local. No PowerShell, gere uma chave uma vez e salve na variável de ambiente do usuário:

```powershell
[Environment]::SetEnvironmentVariable('AUTH_SECRET_KEY', (python -c "import secrets; print(secrets.token_urlsafe(48))"), 'User')
```

Em cada nova sessão do PowerShell, carregue a chave e inicie o backend:

```powershell
$env:AUTH_SECRET_KEY = [Environment]::GetEnvironmentVariable('AUTH_SECRET_KEY', 'User')
powershell -NoProfile -ExecutionPolicy Bypass -File .\Backend\iniciar.ps1
```

Em produção, configure também `APP_ENV=production`, guarde `AUTH_SECRET_KEY` no gerenciador de segredos do ambiente e use HTTPS. A tela de login do frontend usa `/api/login`; o proxy configurado no Vite funciona apenas durante `npm run dev`, então produção precisa encaminhar `/api` ao backend.

## Postman

Importe `postman/ESTOK-Unificada.postman_collection.json` e abra o Collection Runner. Mantenha `base_url` como `http://127.0.0.1:8000`. Faça login com uma conta Admin, copie `access_token` para a variável de coleção `access_token` e execute em até 15 minutos. A coleção aplica esse Bearer token às requisições protegidas; refresh automático ainda não está configurado. Pastas:

```text
ESTOK API
├── Diagnóstico         (2 requisições)
├── Autenticação        (6)
├── Usuários            (18)
├── Localizações        (14)
└── Tarefas - Gestão    (18)
```

As pastas e asserções da collection foram escritas antes da autenticação obrigatória. A variável Bearer foi adicionada, mas os cenários ainda não foram executados contra a versão 0.4.0.

## Migrations e compatibilidade

As versões anteriores não alteravam tabelas; a 0.4.0 adiciona a tabela `RefreshTokens` pela migration `c91e6d54a2f1`. Continua usando o banco de desenvolvimento `estok`, para preservar os dados da base anterior. Não execute `CriacaoBanco.sql` junto com a migration nem aponte essa baseline para um banco de outra origem.

## Validação da versão

Os testes focados em permissões cobrem cadastro administrativo, provisionamento inicial, gestão e execução de tarefas, reatribuição e gestão/consulta de localizações com SQLite isolado. A suíte legada `test_api.py` ainda usa chamadas sem token e precisa ser adaptada às regras atuais. Aplicação da migration no MySQL real e execução da collection no Postman ainda não foram validadas.

Com o ambiente Python ativo, execute na raiz do projeto:

```powershell
python -m pip install -r .\Backend\requirements-dev.txt
cd Backend
python -m unittest -v test_usuarios_permissoes test_tarefas_permissoes test_localizacoes_permissoes
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
