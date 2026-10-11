param(
    [Parameter(Mandatory=$true)][string]$Video,
    [ValidateRange(0,36000)][double]$StartSeconds = 8,
    [ValidateRange(0.1,120)][double]$DurationSeconds = 6,
    [ValidateRange(0.1,30)][double]$FramesPerSecond = 2
)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $Video).Path
$ffmpegPath = (Get-Command ffmpeg -ErrorAction Stop).Source
$runId = [guid]::NewGuid().ToString('N').Substring(0,8)
$outputPath = Join-Path $PSScriptRoot ('frames/' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $runId)
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
$culture = [System.Globalization.CultureInfo]::InvariantCulture
$startText = $StartSeconds.ToString($culture)
$durationText = $DurationSeconds.ToString($culture)
$fpsText = $FramesPerSecond.ToString($culture)
& $ffmpegPath -hide_banner -loglevel error -n -ss $startText -i $sourcePath -t $durationText -vf "fps=$fpsText" -an (Join-Path $outputPath 'frame_%05d.png')
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg取帧失败。输出文件可能不完整。' }
@{
    source = $sourcePath
    start_seconds = $StartSeconds
    duration_seconds = $DurationSeconds
    sampling_fps = $FramesPerSecond
    note = '保留原始帧尺寸；编号代表采样序列，精确源时间需结合原视频时间基核对。'
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputPath 'source.json') -Encoding utf8
Write-Output $outputPath
