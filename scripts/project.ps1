param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'shell')]
    [string]$Action,
    [ValidateSet('app', 'workspace')]
    [string]$Service = 'app'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectDrive = [System.IO.Path]::GetPathRoot($projectRoot)
if ($projectDrive -match '^[cC]:\\') {
    throw '项目位于 C: 盘；项目文件、临时文件和 Docker 数据不得写入 C: 盘。'
}

$projectTempRoot = Join-Path $projectDrive 'YoloongPPT-Temp'
New-Item -ItemType Directory -Force -Path $projectTempRoot | Out-Null
$env:TEMP = $projectTempRoot
$env:TMP = $projectTempRoot
$env:TMPDIR = $projectTempRoot
$runtimeTemp = Join-Path $projectRoot 'runtime\data\tmp'
New-Item -ItemType Directory -Force -Path $runtimeTemp | Out-Null

$dockerSettingsPath = Join-Path $env:APPDATA 'Docker\settings.json'
if (-not (Test-Path -LiteralPath $dockerSettingsPath)) {
    $dockerSettingsPath = Join-Path $env:APPDATA 'Docker\settings-store.json'
}
if (-not (Test-Path -LiteralPath $dockerSettingsPath)) {
    throw '无法读取 Docker Desktop 数据盘配置；为避免写入 C: 盘，拒绝执行 Docker 操作。'
}

$dockerSettings = Get-Content -Raw -LiteralPath $dockerSettingsPath | ConvertFrom-Json
if ($dockerSettings.wslEngineEnabled -eq $true) {
    $dockerDataRoot = [string]$dockerSettings.customWslDistroDir
    if ([string]::IsNullOrWhiteSpace($dockerDataRoot)) {
        throw 'Docker Desktop 使用 WSL 引擎，但未配置可核验的数据盘位置；为避免写入 C: 盘，拒绝执行。'
    }
    $dockerDiskPath = Join-Path $dockerDataRoot 'disk\docker_data.vhdx'
    if (-not (Test-Path -LiteralPath $dockerDiskPath)) {
        throw "无法确认 Docker WSL 数据盘文件存在：$dockerDiskPath；为避免写入 C: 盘，拒绝执行。"
    }
    $dockerDataRoot = $dockerDiskPath
}
else {
    $dockerDataRoot = [string]$dockerSettings.dataFolder
}

$dockerDataRoot = [Environment]::ExpandEnvironmentVariables($dockerDataRoot)
$dockerDataDrive = [System.IO.Path]::GetPathRoot($dockerDataRoot)
if ([string]::IsNullOrWhiteSpace($dockerDataDrive) -or $dockerDataDrive -match '^[cC]:\\') {
    throw "Docker 数据位置无法确认在非 C: 盘（配置：$dockerDataRoot）；拒绝执行 Docker 操作。"
}

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue

if ($dockerCommand) {
    $dockerPath = $dockerCommand.Source
}
else {
    $dockerPath = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
}

if (-not (Test-Path -LiteralPath $dockerPath)) {
    throw '未找到 Docker CLI。请安装并启动 Docker Desktop，或将 docker 加入 PATH。'
}

$dockerDirectory = Split-Path -Parent $dockerPath
$env:PATH = "$dockerDirectory;$env:PATH"
$dockerContext = 'desktop-linux'
$availableContexts = & $dockerPath context ls --format '{{.Name}}'
if ($LASTEXITCODE -ne 0 -or $availableContexts -notcontains $dockerContext) {
    throw '未找到本机 Docker Desktop 的 desktop-linux 上下文；拒绝切换到其他 Docker 数据位置。'
}

Push-Location $projectRoot
try {
    switch ($Action) {
        'start' {
            & $dockerPath --context $dockerContext compose up -d --build workspace app
        }
        'stop' {
            & $dockerPath --context $dockerContext compose down
        }
        'restart' {
            & $dockerPath --context $dockerContext compose up -d --build --force-recreate workspace app
        }
        'status' {
            & $dockerPath --context $dockerContext compose ps
        }
        'logs' {
            & $dockerPath --context $dockerContext compose logs --follow workspace app
        }
        'shell' {
            & $dockerPath --context $dockerContext compose exec $Service sh
        }
    }

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
