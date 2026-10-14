$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    python -m venv (Join-Path $PSScriptRoot "..\.venv")
    if ($LASTEXITCODE -ne 0) { throw "Falha criando ambiente Python." }
}
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Falha instalando dependencias." }
$env:DB_NAME = "estok"
$env:DB_USER = "root"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3306"
$senha = Read-Host "Senha do MySQL root (nao aparece enquanto digita)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($senha)
try { $env:DB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
try {
    & $python preparar_banco.py
    if ($LASTEXITCODE -ne 0) { throw "Falha preparando banco. Confira o erro acima." }
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Falha na migration. Confira o erro acima." }
    Write-Host "Abra http://127.0.0.1:8000/docs - Ctrl+C para encerrar."
    & $python -m uvicorn main:app --host 127.0.0.1 --port 8000
} finally {
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue
}
