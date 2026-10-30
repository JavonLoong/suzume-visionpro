param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$auditRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$sceneRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $auditRoot)).Path
$workspaceRoot = Split-Path -Parent $sceneRoot
$uploadRoot = (Resolve-Path -LiteralPath (Join-Path $workspaceRoot 'suzume-visionpro-publishing\release-assets')).Path
$plan = Get-Content -LiteralPath (Join-Path $auditRoot 'cleanup-plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
$journal = Join-Path $auditRoot 'deleted-files.jsonl'
if (Test-Path -LiteralPath $journal) { throw 'A deletion journal already exists; inspect it before running again.' }

function Assert-Scope([string]$candidate) {
    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    $allowed = $resolved.StartsWith($sceneRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($uploadRoot + '\', [StringComparison]::OrdinalIgnoreCase)
    if (-not $allowed) { throw "Outside cleanup scope: $resolved" }
    if ($resolved.StartsWith((Join-Path $sceneRoot 'visionpro') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Protected Vision Pro project: $resolved" }
    $item = Get-Item -LiteralPath $resolved -Force
    if ($item.PSIsContainer) { throw "Only individual files may be deleted: $resolved" }
    while ($null -ne $item -and $item.FullName.Length -ge $workspaceRoot.Length) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point rejected: $($item.FullName)" }
        $parentPath = Split-Path -Parent $item.FullName
        if (-not $parentPath) { break }
        $item = Get-Item -LiteralPath $parentPath -Force
    }
    return $resolved
}

# Complete all checks before the first destructive operation.
foreach ($row in $plan.files) {
    $resolved = Assert-Scope $row.path
    $item = Get-Item -LiteralPath $resolved
    if ($item.Length -ne $row.bytes) { throw "Size changed: $resolved" }
    if ((Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Content changed: $resolved" }
}
foreach ($row in $plan.protectedFiles) {
    if ((Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Protected file changed: $($row.path)" }
}
Write-Output "Validated $($plan.files.Count) files; $([Math]::Round($plan.totalBytes / 1GB, 3)) GiB planned."
if (-not $Execute) { return }
$removedBytes = [long]0
$removedCount = 0
foreach ($row in $plan.files) {
    $resolved = Assert-Scope $row.path
    Remove-Item -LiteralPath $resolved -Force
    if (Test-Path -LiteralPath $resolved) { throw "Removal failed: $resolved" }
    $removedBytes += [long]$row.bytes
    $removedCount++
    @{path=$resolved; bytes=$row.bytes; reason=$row.reason; deletedAt=(Get-Date).ToString('o')} | ConvertTo-Json -Compress | Add-Content -LiteralPath $journal -Encoding utf8
}
foreach ($row in $plan.protectedFiles) {
    if ((Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Protected file did not survive: $($row.path)" }
}
$result = @{deletedFiles=$removedCount; deletedBytes=$removedBytes; freedGiB=($removedBytes / 1GB); protectedFilesVerified=$plan.protectedFiles.Count; remoteCommit=$plan.remoteCommit; finishedAt=(Get-Date).ToString('o')}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $auditRoot 'cleanup-result.json') -Encoding utf8
$result | ConvertTo-Json
