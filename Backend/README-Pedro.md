# API REST e validação de Pedro

Esta entrega está na branch `Pedro` e parte da branch `Carlos`. Contém os 17 métodos de itens, QR Code e execução/conferência de tarefas definidos em `Pedro_API_REST_Validacao.md`.

## Arquitetura

`main.py` registra as rotas em `pedro_api/routers`; as regras de negócio ficam em `pedro_api/services`; as consultas e gravações SQLAlchemy ficam em `pedro_api/repositories`; `pedro_api/db.py` fornece sessões para os modelos MySQL existentes de Carlos. O mesmo conjunto de rotas pode rodar sozinho por `pedro_main.py`.

Os esquemas Pydantic em `pedro_api/schemas.py` validam entradas e documentam saídas. Os erros de domínio usam HTTP 404 e 409; falhas de banco usam 503; exclusões bem sucedidas usam 204; cadastros usam 201. O FastAPI publica a documentação em `/docs` e `/openapi.json`.

## Execução

Na pasta `Backend`, instale as dependências de `requirements-pedro.txt`. Configure `DATABASE_URL` para a conexão SQLAlchemy do seu MySQL e aplique as migrations do projeto antes de iniciar. Exemplo de URL: `mysql+mysqlconnector://usuario:senha@localhost:3306/estok`.

```powershell
pip install -r requirements-pedro.txt
$env:DATABASE_URL = 'mysql+mysqlconnector://usuario:senha@localhost:3306/estok'
uvicorn main:app --reload
```

O `main.py` de Carlos mantém suas rotas iniciais. `pedro_main:app` expõe apenas a parte de Pedro, útil para Swagger e validação isolada.

## Collection Postman

Importe `postman/ESTOK-Pedro.postman_collection.json`. Ela executa 22 requisições sequenciais: os 17 métodos previstos mais 5 casos de erro. Ajuste `baseUrl` e `taskId` nas variáveis da Collection. `taskId` precisa apontar para uma tarefa com estado `Pendante` e sem itens. A Collection cria e exclui um item de exemplo.

Para criar uma tarefa temporária em um **banco de teste já migrado**, configure `DATABASE_URL` para esse banco e execute:

```powershell
python preparar_validacao_pedro.py
```

Use o `taskId` impresso na variável da Collection. Para Newman:

```powershell
newman run postman/ESTOK-Pedro.postman_collection.json --env-var baseUrl=http://127.0.0.1:8000 --env-var taskId=1
```

## Limites da validação

A Collection passou em SQLite temporário, com 22 requisições e 34 afirmações. A integração com MySQL real e as migrations de Carlos ainda dependem do banco configurado pelo grupo. O backend de Carlos já contém credenciais fixas em `banco.py` e sua migration deve ser revisada antes de rodar em um banco com dados.
