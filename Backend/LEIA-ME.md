# ESTOK — João e Felipe — Backend e Swagger

## Instalar e iniciar no Windows

Copie a pasta Backend deste pacote para a raiz do seu projeto, na branch joao. Se já houver Backend com trabalho local, faça backup antes de substituir. Acrescente ao .gitignore da raiz: `.venv/`, `__pycache__/`, `*.py[cod]` e `.env`.

No PowerShell, na raiz do projeto:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Backend\iniciar.ps1
```

A opção Bypass vale somente para esse processo. O script instala as dependências, pede a senha do root, cria o banco separado estok_joao, executa Alembic e inicia a API. A senha fica apenas no ambiente do processo e não é gravada no código. O serviço MySQL80 precisa estar Running. Feche com Ctrl+C.

Abra http://127.0.0.1:8000/docs. OpenAPI: http://127.0.0.1:8000/openapi.json.

## Testar no Swagger

1. GET /saude → 200.
2. GET /saude/banco → 200.
3. POST /usuarios → Try it out, use o JSON abaixo e Execute → 201.
4. POST /login com o mesmo email/senha → 200; senha incorreta → 401.
5. Repetir cadastro com mesmo email → 409.
6. PUT /usuarios/{id} com ID retornado e todos os campos → 200; ID -1 → 404.
7. Cadastro com email inválido ou senha menor que 8 caracteres → 422.

```json
{"nome":"João Teste","email":"joao.teste@example.com","senha":"TesteLocal123!","perfil":"Funcionario"}
```

A senha acima é só do usuário de teste da API, não a senha root do MySQL.

## Postman

Importe ESTOK.postman_collection.json e execute no Collection Runner, na ordem. Cada execução cria um novo usuário de teste. Há 9 requisições para as rotas disponíveis. Os testes verificam status HTTP e ausência de senha na resposta. Não representa validação dos 20 endpoints da lista.

## Escopo e pendências

Foram corrigidas as três rotas já iniciadas pelo Carlos: POST /login (item 1), POST /usuarios (item 10), PUT /usuarios/{id} (item 11). As outras 17 rotas dependem do colega responsável pela API. /saude e /saude/banco são auxiliares.

Modelos SQLAlchemy e Pydantic foram separados; importações e caminho PUT corrigidos; usuários persistem no banco e senhas usam PBKDF2. Respostas não expõem senhas. Login ainda NÃO fornece sessão/token e as rotas ainda NÃO exigem autenticação/autorização: pendência para o colega, uso local acadêmico.

## Migrations

Este pacote usa nova baseline joao_baseline_01 somente no banco estok_joao. Não substitua o histórico de um banco existente pelo do pacote. O preparador recusa bancos com tabelas e sem essa revisão. Não executar CriacaoBanco.sql junto com a migration. Os nomes de campos e relacionamentos originais foram preservados, inclusive tituto e Pendante; alterações do grupo exigem migrations futuras.

## Validação realizada neste ambiente

5 testes automatizados passaram (Swagger/OpenAPI, persistência e login, validação 422, tratamento 503 e saúde), usando SQLite e Python 3.12. O SQL da migration foi gerado no dialeto MySQL, contendo 5 tabelas do projeto e a tabela Alembic, sem DROP TABLE no upgrade. MySQL real, Python 3.13 e PowerShell devem ser confirmados no PC de João. A Collection foi preparada, mas não executada no aplicativo Postman.

Para repetir os testes:

```powershell
cd Backend
..\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
..\.venv\Scripts\python.exe -m unittest -v test_api
```

## Subir para a branch joao após testar

Na raiz do projeto, confirme `git branch --show-current` retorna joao, então:

```powershell
git status --short
git add Backend .gitignore
git diff --cached --stat
git commit -m "Corrige backend e configura Swagger e migrations de desenvolvimento"
git push origin joao
```

Se o push for rejeitado por atualizações remotas, não use force: revise e integre as alterações primeiro. Não inclua .venv ou credenciais no commit.
