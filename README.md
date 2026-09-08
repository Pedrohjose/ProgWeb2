# ESTOK
Trabalho de programação Web 2

Sistema de gerenciamento de patrimonio, que gera etiquetas QrCode e possibilita a conferencia de material por meio de tasks

Para rodar o projeto precisa de:<br>
* Node.js<br>
* Instalar o Tailwind CSS no projeto pelo Node.js <br>
  * Usando o comando a seguir DENTRO da pasta do projeto:<br> npm install tailwindcss @tailwindcss/vite
* Apos concluir os passos anteriores para rodar o projeto, basta pelo terminal, acessar a pasta do projeto, e executar o comando:
  * npm run dev

Telas feitas: 
  - [x] POST /login
  - [x] GET /itens/{all}
  - [x] GET /itens/{id}
  - [x] POST /itens
  - [x] PUT /itens/{id}
  - [x] DELETE /itens/{id}
  - [x] GET /itens/{id}/qrcode
  - [x] POST /itens/{id}/qrcode
  - [x] GET /qrcode/{codigo}
  - [x] GET /qrcode/{all}
  - [x] GET /tarefas/{all}
  - [x] GET /tarefas/{id}
  - [x] POST /tarefas
  - [x] PUT /tarefas/{id}
  - [x] DELETE /tarefas/{id}
  - [x] POST /tarefas/{id}/iniciar
  - [x] POST /tarefas/{id}/concluir
  - [x] GET /tarefas/{id}/progresso
  - [x] PUT /tarefas/{id}/atribuir/{usuarioId}
  - [x] GET /tarefas/{id}/itens/{all}
  - [x] GET /tarefas/{id}/itens/{itemId}
  - [x] POST /tarefas/{id}/itens/{itemId}
  - [x] DELETE /tarefas/{id}/itens/{itemId}
  - [x] POST /tarefas/{id}/itens/{itemId}/conferir
  - [x] GET /usuarios/{all}
  - [x] GET /usuarios/{id}
  - [x] POST /usuarios
  - [x] PUT /usuarios/{id}
  - [x] DELETE /usuarios/{id}
  - [x] GET /usuarios/{id}/tarefas/{all}
  - [x] GET /localizacoes/{all}
  - [x] GET /localizacoes/{id}
  - [x] POST /localizacoes
  - [x] PUT /localizacoes/{id}
  - [x] DELETE /localizacoes/{id}
  - [x] GET /localizacoes/{id}/itens/{all}
  - [x] GET /localizacoes/{id}/qrcode/{all}
  
## E assim ele ira iniciar o projeto

**[Documentação Tillwind](https://tailwindcss.com/plus/ui-blocks?ref=sidebar)**