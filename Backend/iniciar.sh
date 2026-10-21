#!/bin/bash
set -e  # Para o script imediatamente se qualquer comando falhar (equivalente ao $ErrorActionPreference = 'Stop')

# Caminho onde o script está localizado
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuração do ambiente virtual (venv)
VENV="$HOME/.local/share/EstokPedro/venv"
PYTHON="$VENV/bin/python"

# Verifica se o Python do venv existe, se não, tenta criar
if [ ! -f "$PYTHON" ]; then
    if command -v python3 &>/dev/null; then
        python3 -m venv "$VENV"
    else
        # Fallback para o caminho do cache que você usava no Windows (adaptado para a estrutura Linux se existir)
        BUNDLED_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
        if [ ! -f "$BUNDLED_PYTHON" ]; then
            echo "Erro: Python não encontrado. Instale o python3-venv no sistema."
            exit 1
        fi
        $BUNDLED_PYTHON -m venv "$VENV"
    fi
fi

# Instala as dependências
$PYTHON -m pip --disable-pip-version-check install --quiet -r requirements.txt

# Verifica se o serviço do MySQL está rodando no Ubuntu
if ! systemctl is-active --quiet mysql; then
    echo "Erro: O serviço do MySQL está parado. Inicie-o com: sudo systemctl start mysql"
    exit 1
fi

# Configuração das variáveis de ambiente do banco
export DB_NAME="estok"
export DB_USER="root"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"

# Solicita a senha de forma segura (mascara o input)
echo -n "Senha local do MySQL root: "
read -s DB_PASSWORD
echo "" # Apenas pula a linha após o enter da senha
export DB_PASSWORD

# Executa o teste do banco e inicia o Uvicorn
try_run() {
    # Tenta rodar o comando Python do SQLAlchemy
    $PYTHON -c "from sqlalchemy import text; from banco import engine; connection = engine.connect(); connection.execute(text('SELECT 1 FROM Itens LIMIT 1')); connection.close(); print('Banco estok pronto')"
    
    echo "Swagger: http://127.0.0.1:8000/docs"
    $PYTHON -m uvicorn main:app --host 127.0.0.1 --port 8000
}

# Garante que a senha será apagada da memória ao fechar o script (equivalente ao bloco 'finally')
trap 'unset DB_PASSWORD' EXIT

try_run