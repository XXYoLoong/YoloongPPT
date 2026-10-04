param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'shell')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
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

Push-Location $projectRoot
try {
    switch ($Action) {
        'start' {
            & $dockerPath compose up -d --build workspace
        }
        'stop' {
            & $dockerPath compose down
        }
        'restart' {
            & $dockerPath compose up -d --build --force-recreate workspace
        }
        'status' {
            & $dockerPath compose ps
        }
        'logs' {
            & $dockerPath compose logs --follow workspace
        }
        'shell' {
            & $dockerPath compose exec workspace bash
        }
    }

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
