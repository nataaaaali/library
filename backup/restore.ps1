# ============================================================
# Скрипт восстановления БД АИС "Библиотека" из резервной копии
# ============================================================

param(
    [string]$BackupFile,
    [string]$DbName     = $env:DB_NAME,
    [string]$DbUser     = $env:DB_USER,
    [string]$DbPassword = $env:DB_PASSWORD,
    [string]$DbHost     = "localhost",
    [string]$BackupDir  = ".\backups"
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

# --- Ищем pg_restore ---
$pgRestorePaths = @(
    "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe",
    "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe",
    "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe",
    "C:\Program Files\PostgreSQL\15\bin\pg_restore.exe",
    "pg_restore.exe"
)

$pgRestore = $null
foreach ($path in $pgRestorePaths) {
    if (Test-Path $path) {
        $pgRestore = $path
        break
    }
}

if (-not $pgRestore) {
    Write-Error "pg_restore.exe не найден. Установите PostgreSQL или добавьте bin в PATH."
    exit 1
}

# --- Интерактивный выбор копии (если файл не указан) ---
if (-not $BackupFile) {
    Write-Info "Файл бэкапа не указан. Ищу доступные копии..."

    if (-not (Test-Path $BackupDir)) {
        Write-Error "Папка с бэкапами не найдена: $BackupDir"
        exit 1
    }

    $backups = Get-ChildItem -Path $BackupDir -Filter "backup_*.dump" | Sort-Object LastWriteTime -Descending

    if ($backups.Count -eq 0) {
        Write-Error "В папке $BackupDir не найдено файлов бэкапов."
        exit 1
    }

    Write-Host ""
    Write-Host "  Доступные резервные копии:" -ForegroundColor White
    Write-Host "  ---- ------------------- --------  ------------------------------" -ForegroundColor DarkGray

    $i = 1
    foreach ($b in $backups) {
        $num  = $i.ToString().PadLeft(2)
        $date = $b.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
        $size = (Format-Size $b.Length).PadRight(8)
        Write-Host "  $num  $date  $size  $($b.Name)" -ForegroundColor White
        $i++
    }

    Write-Host ""
    $choice = Read-Host "  Введите номер копии для восстановления"

    if ($choice -notmatch '^\d+$') {
        Write-Error "Нужно ввести число."
        exit 1
    }

    $idx = [int]$choice - 1
    if ($idx -lt 0 -or $idx -ge $backups.Count) {
        Write-Error "Неверный номер. Выберите от 1 до $($backups.Count)."
        exit 1
    }

    $BackupFile = $backups[$idx].FullName
    Write-Info "Выбран: $($backups[$idx].Name)"
}

# --- Проверяем наличие файла ---
if (-not (Test-Path $BackupFile)) {
    Write-Error "Файл бэкапа не найден: $BackupFile"
    exit 1
}

# --- Подтверждение ---
Write-Host ""
Write-Host "  =============================================" -ForegroundColor Yellow
Write-Host "    ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ АИС 'Библиотека'" -ForegroundColor Yellow
Write-Host "  =============================================" -ForegroundColor Yellow
Write-Host ""
Write-Info "База данных: $DbName"
Write-Info "Файл бэкапа: $BackupFile"
Write-Host ""
Write-Error "ВНИМАНИЕ: текущая база данных будет ПОЛНОСТЬЮ заменена"
Write-Error "данными из резервной копии. Все изменения после даты"
Write-Error "бэкапа будут утеряны."
Write-Host ""

$confirm = Read-Host "  Введите 'YES' для продолжения восстановления"
if ($confirm -ne "YES") {
    Write-Warning "Восстановление отменено."
    exit 0
}

# --- Восстановление ---
$env:PGPASSWORD = $DbPassword

try {
    Write-Host ""
    Write-Info "Начинается восстановление..."

    & $pgRestore -h $DbHost -U $DbUser -d $DbName -c -v "$BackupFile"

    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {
        Write-Host ""
        Write-Success "Восстановление завершено."
        Write-Warning "Перезапустите серверное приложение (uvicorn)."
    } else {
        Write-Host ""
        Write-Error "Восстановление завершилось с кодом $LASTEXITCODE. Проверьте вывод выше."
        exit 1
    }
}
catch {
    Write-Host ""
    Write-Error "Ошибка во время восстановления: $_"
    exit 1
}
finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
