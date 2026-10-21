#!/bin/bash

# 1. Garante que o script pare se houver algum erro drástico
set -e

# 2. Descobre a pasta onde o script está e entra nela
cd estok/ProbWeb2

echo "=== 1. Verificando Banco de Dados ==="
# Inicia o MySQL caso esteja parado (pode pedir sua senha do Linux no terminal)
if ! systemctl is-active --quiet mysql; then
    echo "Iniciando o serviço do MySQL..."
    sudo systemctl start mysql
echo "MySQL pronto e rodando!"

echo ""
echo "=== 2. Ativando Ambiente Python ==="
# Cria o venv se ele não existir na pasta atual
python3 -m venv venv
source venv/bin/activate

echo "Verificando dependências (requirements.txt)..."
pip install --quiet -r requirements.txt

echo ""
echo "=== 3. Configurando Banco e Inicializando API ==="

export DB_NAME="estok"
export DB_USER="root"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"

# Pede a senha do banco de forma segura (sem exibir o que você digita)
echo -n "Senha=2709!"
read -s DB_PASSWORD
echo "" # Pula a linha após o Enter
export DB_PASSWORD

# Garante que a senha suma das variáveis de ambiente quando o script fechar
trap 'unset DB_PASSWORD' EXIT

echo "Iniciando Uvicorn na porta 8000..."
echo "Swagger disponível em: http://40.127.11.169:8000/docs"
echo "Pressione Ctrl+C para encerrar o servidor."
echo "------------------------------------------------"

# Executa o Uvicorn (removido o 'set -e' interno para o Ctrl+C fechar graciosamente)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
