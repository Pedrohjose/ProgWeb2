#!/bin/bash

# 1. Garante que o script pare se houver algum erro drástico
set -e

# CORREÇÃO: Certifique-se de que a pasta é ProgWeb2 (com 'g' e não 'b') se seguir o padrão anterior
cd ~/estok/ProgWeb2/Backend 2>/dev/null || cd estok/ProbWeb2/Backend

echo "=== 1. Verificando Banco de Dados ==="
# Inicia o MySQL caso esteja parado
if ! systemctl is-active --quiet mysql; then
    echo "Iniciando o serviço do MySQL..."
    sudo systemctl start mysql
fi # CORREÇÃO 1: Faltava fechar o 'if' com 'fi' aqui

echo "MySQL pronto e rodando!"

echo ""
echo "=== 2. Ativando Ambiente Python ==="
# Cria o venv se ele não existir na pasta atual
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "Verificando dependências..."
pip install --quiet -r requirements.txt

echo ""
echo "=== 3. Configurando Banco e Inicializando API ==="

export DB_NAME="ESTOK"
export DB_USER="root"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"

# CORREÇÃO 2: Define a senha padrão caso o usuário apenas aperte ENTER
echo -n "Digite a senha do banco (Padrão: Senha=2709!): "
read -s ENTRADA_SENHA
echo "" 

if [ -z "$ENTRADA_SENHA" ]; then
    export DB_PASSWORD="senha123"
else
    export DB_PASSWORD="$ENTRADA_SENHA"
fi

# Garante que a senha suma das variáveis de ambiente quando o script fechar
trap 'unset DB_PASSWORD' EXIT

echo "Iniciando Uvicorn na porta 8000..."
echo "Swagger disponível em: http://40.127.11.169:8000/docs"
echo "Pressione Ctrl+C para encerrar o servidor."
echo "------------------------------------------------"

# Executa o Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
