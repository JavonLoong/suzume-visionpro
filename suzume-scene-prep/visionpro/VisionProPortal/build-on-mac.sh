#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "$(uname -s)" != Darwin ]]; then
  echo '请在安装了 Xcode 与 visionOS SDK 的 Mac 上执行此脚本。' >&2
  exit 1
fi
command -v xcodebuild >/dev/null || { echo '未找到 Xcode。' >&2; exit 1; }
mkdir -p BuildLogs
# 无需开发者签名的模拟器编译；不会安装到头显或上传任何内容。
xcodebuild -project VisionProPortal.xcodeproj -scheme VisionProPortal \
  -configuration Debug -sdk xrsimulator -destination 'generic/platform=visionOS Simulator' \
  -derivedDataPath DerivedData CODE_SIGNING_ALLOWED=NO build 2>&1 | tee BuildLogs/simulator-build.log
