param([ValidatePattern('^[A-Z_][A-Z0-9_]*$')][string]$ApiKeyEnvironment = 'DEEPSEEK_API_KEY')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectDrive = [IO.Path]::GetPathRoot($projectRoot)
if ($projectDrive -match '^[cC]:\\') { throw '模型凭据和临时目录不得放在C盘。' }
$env:TEMP = Join-Path $projectDrive 'YoloongPPT-Temp'
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
$providerCredential = $null
foreach ($credentialScope in @('Process', 'User', 'Machine')) {
    $providerCredential = [Environment]::GetEnvironmentVariable($ApiKeyEnvironment, $credentialScope)
    if (-not [string]::IsNullOrWhiteSpace($providerCredential)) { break }
}
if ([string]::IsNullOrWhiteSpace($providerCredential)) { throw '指定环境变量中没有模型凭据，未创建空配置。' }
$credentialFolder = Join-Path $projectRoot 'runtime\data\secrets'
New-Item -ItemType Directory -Force -Path $credentialFolder | Out-Null
[IO.File]::WriteAllText((Join-Path $credentialFolder 'deepseek_api_key'), $providerCredential, [Text.UTF8Encoding]::new($false))
Remove-Variable providerCredential
Write-Output '授权环境变量已同步到F盘忽略目录。容器按文件读取，密钥没有写入Git、镜像或输出。'
