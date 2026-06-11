# ============================================================
# Скрипт резервного копирования БД АИС "Библиотека"
# ============================================================

param(
    [string]$DbName = $env:DB_NAME,
    [string]$DbUser = $env:DB_USER,
    [string]$DbPassword = $env:DB_PASSWORD,
    [string]$BackupDir = ".\backups",
    [int]$KeepDays = 30
)

# Значения по умолчанию, если переменные окружения не заданы
if (-not $DbName)     { $DbName     = "library_db" }
if (-not $DbUser)     { $DbUser     = "postgres" }
if (-not $DbPassword) { $DbPassword = "12345" }

$ErrorActionPreference = "Stop"

# --- Вспомогательные функции вывода ---
function Write-Info($msg)    { Write-Host "  [.] $msg" -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host "  [+] $msg" -ForegroundColor Green }
function Write-Warning($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Error($msg)   { Write-Host "  [-] $msg" -ForegroundColor Red }

function Format-Size($bytes) {
    if ($bytes -ge 1GB) { return "{0:N2} GB" -f ($bytes / 1GB) }
    if ($bytes -ge 1MB) { return "{0:N2} MB" -f ($bytes / 1MB) }
    if ($bytes -ge 1KB) { return "{0:N2} KB" -f ($bytes / 1KB) }
    return "$bytes B"
}

# --- Ищем pg_dump ---
$pgDumpPaths = @(
    "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
    "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
    "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
    "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
    "pg_dump.exe"
)

$pgDump = $null
foreach ($path in $pgDumpPaths) {
    if (Test-Path $path) {
        $pgDump = $path
        break
    }
}

if (-not $pgDump) {
    Write-Error "pg_dump.exe не найден. Установите PostgreSQL или добавьте bin в PATH."
    exit 1
}

# --- Создаем папку для бэкапов ---
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
    Write-Info "Создана папка: $BackupDir"
}

$timestamp  = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupFile = Join-Path $BackupDir "backup_${timestamp}.dump"
$logFile    = Join-Path $BackupDir "backup.log"

# --- Запускаем pg_dump ---
$env:PGPASSWORD = $DbPassword
try {
    Write-Info "Создание бэкапа: backup_${timestamp}.dump ..."

    & $pgDump -h localhost -U $DbUser -F c -f $backupFile $DbName
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump завершился с кодом $LASTEXITCODE"
    }

    $size = Format-Size (Get-Item $backupFile).Length
    $msg  = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') SUCCESS: $backupFile ($size)"
    Add-Content -Path $logFile -Value $msg
    Write-Success "Бэкап создан: $backupFile ($size)"
}
catch {
    $msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ERROR: $_"
    Add-Content -Path $logFile -Value $msg
    Write-Error $msg
    exit 1
}
finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

# --- Удаляем старые бэкапы ---
$cutoffDate = (Get-Date).AddDays(-$KeepDays)
$removed    = Get-ChildItem -Path $BackupDir -Filter "backup_*.dump" | Where-Object {
    $_.LastWriteTime -lt $cutoffDate
}

if ($removed) {
    foreach ($file in $removed) {
        Remove-Item $file.FullName -Force
        $msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') CLEANUP: удален $($file.Name)"
        Add-Content -Path $logFile -Value $msg
        Write-Warning "Удален старый бэкап: $($file.Name)"
    }
}

Write-Success "Готово."
