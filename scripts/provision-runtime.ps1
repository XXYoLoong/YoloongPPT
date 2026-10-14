param([ValidateSet('all','wheels','models')][string]$Selection='all')
$ErrorActionPreference='Stop'
$taskProjectRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
if ([IO.Path]::GetPathRoot($taskProjectRoot) -match '^[cC]:\\') {throw '运行依赖和模型缓存必须在非 C: 盘。'}
$taskCacheRoot=Join-Path $taskProjectRoot 'runtime\data'
$taskTempRoot=Join-Path $taskCacheRoot 'tmp'
New-Item -ItemType Directory -Force -Path $taskTempRoot | Out-Null
$env:TEMP=$taskTempRoot; $env:TMP=$taskTempRoot
$taskAllowedHosts=@('files.pythonhosted.org','download.pytorch.org','download-r2.pytorch.org','huggingface.co','www.modelscope.cn')
function Save-VerifiedArtifact([string]$Relative,[string]$Url,[string]$ExpectedHash,[string]$Base) {
    $taskDestination=[IO.Path]::GetFullPath((Join-Path $Base $Relative))
    $taskPrefix=[IO.Path]::GetFullPath($Base).TrimEnd('\')+'\'
    if (-not $taskDestination.StartsWith($taskPrefix,[StringComparison]::OrdinalIgnoreCase)) {throw '缓存清单路径越界。'}
    $taskUri=[Uri]$Url
    if ($taskUri.Scheme -ne 'https' -or $taskUri.Host -notin $taskAllowedHosts -or $ExpectedHash -notmatch '^[a-f0-9]{64}$') {throw '下载来源或固定 SHA256 无效。'}
    if (Test-Path -LiteralPath $taskDestination) {
        if ((Get-FileHash -LiteralPath $taskDestination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedHash) {throw "缓存文件改变：$Relative；保留原文件并停止。"}
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $taskDestination) | Out-Null
    $taskPartial=$taskDestination+'.download'
    & curl.exe --silent --show-error --fail --location --retry 2 --max-time 180 --output $taskPartial $Url
    if ($LASTEXITCODE -ne 0) {throw "固定来源下载失败：$Relative"}
    if ((Get-FileHash -LiteralPath $taskPartial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedHash) {throw "下载 SHA256 不符：$Relative；未发布缓存。"}
    Move-Item -LiteralPath $taskPartial -Destination $taskDestination
}
if ($Selection -in @('all','wheels')) {
    $taskWheelManifest=Get-Content -LiteralPath (Join-Path $taskProjectRoot 'config\runtime-wheels.json') -Raw -Encoding utf8 | ConvertFrom-Json
    foreach ($taskArtifact in $taskWheelManifest.files) {
        Save-VerifiedArtifact $taskArtifact.filename $taskArtifact.url $taskArtifact.sha256 (Join-Path $taskCacheRoot 'dependency-wheels')
    }
    Write-Output "已核验 $($taskWheelManifest.files.Count) 个固定 Linux 运行依赖；主机未安装产品依赖。"
}
if ($Selection -in @('all','models')) {
    $taskModelManifest=Get-Content -LiteralPath (Join-Path $taskProjectRoot 'config\docling-models.json') -Raw -Encoding utf8 | ConvertFrom-Json
    foreach ($taskArtifact in $taskModelManifest.files) {
        Save-VerifiedArtifact $taskArtifact.relative_path $taskArtifact.source_url $taskArtifact.actual_sha256 (Join-Path $taskCacheRoot 'cache\docling\models')
    }
    Write-Output "已核验 $($taskModelManifest.files.Count) 个固定 Docling 模型/配置文件。"
}
