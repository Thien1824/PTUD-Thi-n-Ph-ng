# Install script for PageSpark
# ---------------------------------------------------
# Always run from repository root, even if the script is started from scripts\
Set-Location (Join-Path $PSScriptRoot "..")

# 1. Find Python executable
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} else {
    Write-Host "Python không tìm thấy. Vui lòng cài Python hoặc đảm bảo 'python'/'py' trên PATH." -ForegroundColor Red
    exit 1
}

# 2. Create virtual environment if needed
$venvPath = "backend\venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path -Path $venvPath)) {
    Write-Host "Tạo virtual environment tại: $venvPath"
    if ($pythonCmd -eq 'py') {
        & $pythonCmd -3 -m venv $venvPath
    } else {
        & $pythonCmd -m venv $venvPath
    }
}

if (-not (Test-Path -Path $venvPython)) {
    Write-Host "Không tìm thấy python trong virtual environment: $venvPython" -ForegroundColor Red
    exit 1
}

# 3. Use the venv python for all actions
$pythonExec = $venvPython

# 4. Upgrade pip inside venv
Write-Host "Cập nhật pip trong venv..."
& $pythonExec -m pip install --upgrade pip

# 5. Install dependencies
Write-Host "Cài đặt dependencies từ backend\requirements.txt..."
& $pythonExec -m pip install -r backend\requirements.txt

# 6. Init database
Write-Host "Khởi tạo database và tài khoản admin..."
& $pythonExec -c "from backend.database import init_db; init_db()"

# 7. Start backend with uvicorn from the virtual environment
Write-Host "Khởi chạy backend..."
Start-Process -FilePath $pythonExec -ArgumentList '-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000' -NoNewWindow

# 8. Open frontend
Start-Process "frontend\index.html"

Write-Host "✅ Cài đặt hoàn tất! Backend đang chạy tại http://localhost:8000" -ForegroundColor Green
