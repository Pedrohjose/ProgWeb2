# ESTOK

Projeto de Programação Web 2: sistema de gerenciamento de patrimônio, com cadastro de usuários, itens, localizações e tarefas de conferência.

## API e documentação

A base atual oferece **6 dos 20 endpoints do escopo de autenticação, usuários, tarefas e localizações**: login e CRUD de usuários. Há também duas rotas auxiliares de diagnóstico.

- **[Guia de execução e testes do backend](Backend/README.md)**
- **[Collection do Postman](Backend/ESTOK.postman_collection.json)**
- Com o backend iniciado, acesse **http://127.0.0.1:8000/docs** para abrir **ESTOK — Swagger de Testes**.

As instruções incluem preparação do MySQL, migrations, exemplos, respostas de erro e testes. A existência de telas HTML não significa que todas as rotas da API já estejam implementadas.

## Frontend

Com Node.js instalado, na raiz do projeto:

```powershell
npm ci
npm run dev
```

Abra o endereço informado pelo Vite. Frontend e API são processos separados; a integração de todas as telas com o backend permanece parte do desenvolvimento do grupo.

## Continuidade

A versão 0.2.0 da base mantém o banco de desenvolvimento `estok_joao` e o histórico de migrations. O grupo continuará os 14 endpoints pendentes desse escopo e definirá a autenticação/autorização final.
