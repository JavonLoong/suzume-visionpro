param([switch]$BuildTests)
$ErrorActionPreference='Stop'
$nativeRoot=$PSScriptRoot
$projectRoot=Split-Path (Split-Path $nativeRoot -Parent) -Parent
$toolchain='D:\Unity\Editors\2022.3.62f3\Editor\Data\PlaybackEngines\AndroidPlayer\NDK\android-ndk-r23b\toolchains\llvm\prebuilt\windows-x86_64'
$compiler=Join-Path $toolchain 'bin\clang++.exe'
$common=@('--target=aarch64-linux-android29',"--sysroot=$toolchain\sysroot",'-std=c++17','-O2','-fno-exceptions','-fno-rtti','-nostdlib++','-Wall','-Wextra','-Werror',"-I$nativeRoot")
$output=Join-Path $projectRoot 'Assets\Plugins\Android\arm64-v8a\libPortalPassthrough.so'
& $compiler @common '-shared' '-fPIC' '-fvisibility=hidden' '-Wl,--no-undefined' '-Wl,-soname,libPortalPassthrough.so' (Join-Path $nativeRoot 'portal_passthrough.cpp') '-llog' '-o' $output
if($LASTEXITCODE -ne 0) { throw 'Composition native plugin compilation failed' }
if($BuildTests)
{
    $testOutput=Join-Path $projectRoot 'Builds\controller-check\portal_composition_test'
    & $compiler @common (Join-Path $nativeRoot 'portal_passthrough_test.cpp') '-llog' '-o' $testOutput
    if($LASTEXITCODE -ne 0) { throw 'Composition native test compilation failed' }
}
Get-Item -LiteralPath $output | Select-Object FullName,Length
