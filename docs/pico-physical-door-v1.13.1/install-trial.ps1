param(
    [string]$Serial = '',
    [string]$BoardAddress = '',
    [string]$Adb = 'D:/Unity/Editors/2022.3.62f3/Editor/Data/PlaybackEngines/AndroidPlayer/SDK/platform-tools/adb.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Adb)) {
    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    if (-not $adbCommand) { throw 'adb was not found. Supply -Adb with its full path.' }
    $Adb = $adbCommand.Source
}
if ($BoardAddress -and $BoardAddress -notmatch '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$') { throw 'Invalid BLE address.' }
$info = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'version.json') -Raw | ConvertFrom-Json
$apk = Join-Path $PSScriptRoot $info.apk
if ((Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLowerInvariant() -ne $info.apk_sha256) { throw 'APK checksum mismatch.' }
$deviceList = @(& $Adb devices)
if ($LASTEXITCODE -ne 0) { throw 'Cannot query adb devices.' }
$connected = @($deviceList | Where-Object { $_ -match '^([^\s]+)\s+device\s*$' } | ForEach-Object { ($_ -split '\s+')[0] } | Where-Object { $_ -notlike 'emulator-*' })
if (-not $Serial) {
    $headsets = @()
    foreach ($candidate in $connected) {
        $identity = (& $Adb -s $candidate shell getprop ro.product.manufacturer) + (& $Adb -s $candidate shell getprop ro.product.model)
        if (($identity -join ' ') -match '(?i)pico') { $headsets += $candidate }
    }
    if ($headsets.Count -ne 1) { throw 'Connect exactly one PICO with USB debugging allowed, or supply -Serial.' }
    $Serial = $headsets[0]
}
if ($Serial -notin $connected) { throw 'The specified physical headset is not connected/authorized.' }
$model = (& $Adb -s $Serial shell getprop ro.product.manufacturer) + (& $Adb -s $Serial shell getprop ro.product.model)
if (($model -join ' ') -notmatch '(?i)pico') { throw 'Target is not identified as PICO. Installation stopped.' }
& $Adb -s $Serial install -r $apk
if ($LASTEXITCODE -ne 0) { throw 'Installation failed. No existing app has been uninstalled. Check signature/version errors.' }
$launch = @('-s', $Serial, 'shell', 'am', 'start', '-S', '-n', 'com.suzume.portal.bletrial/com.unity3d.player.UnityPlayerActivity')
if ($BoardAddress) { $launch += @('--es', 'com.suzume.door.BOARD_ADDRESS', $BoardAddress.ToUpperInvariant()) }
& $Adb @launch
if ($LASTEXITCODE -ne 0) { throw 'Installed, but launch failed.' }
Write-Output 'Trial installed and started. BLE connects and queries only; this script never sends open/reset commands.'
