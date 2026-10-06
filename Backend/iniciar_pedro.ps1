$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$venv = Join-Path $env:LOCALAPPDATA 'EstokPedro\venv'
$python = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        & py -3 -m venv $venv
    } else {
        $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (-not (Test-Path -LiteralPath $bundledPython)) {
            throw 'Python nao encontrado. Instale Python 3 ou informe o caminho de um python.exe neste script.'
        }
        & $bundledPython -m venv $venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o ambiente Python.' }
}

& $python -m pip --disable-pip-version-check install --quiet -r requirements-pedro.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias da API.' }

$mysql = Get-Service MySQL80 -ErrorAction SilentlyContinue
if (-not $mysql -or $mysql.Status -ne 'Running') {
    throw 'MySQL80 esta parado. Inicie-o em um PowerShell administrador com: Start-Service MySQL80'
}

$env:DB_NAME = 'estok'
$env:DB_USER = 'root'
$env:DB_HOST = '127.0.0.1'
$env:DB_PORT = '3306'
$senha = Read-Host 'Senha local do MySQL root' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($senha)
try { $env:DB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }

try {
    & $python -c "from sqlalchemy import text; from banco import engine; connection = engine.connect(); connection.execute(text('SELECT 1 FROM Itens LIMIT 1')); connection.close(); print('Banco estok pronto')"
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao acessar o banco estok ou a tabela Itens.' }

    Write-Host 'Swagger: http://127.0.0.1:8000/docs'
    & $python -m uvicorn pedro_main:app --host 127.0.0.1 --port 8000
} finally {
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue
}
