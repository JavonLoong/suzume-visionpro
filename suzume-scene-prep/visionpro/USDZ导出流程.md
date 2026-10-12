# v56 到 Vision Pro 的可复现导出

源文件：`../character-hunyuan-v1/poster-right-bow-v56/Suzume_dual_scene_right_bow_v56.blend`。工具只读取源模型，不保存或覆盖它。

## 导出与验证

Windows PowerShell 示例，在 `visionpro` 目录执行：

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --threads 4 --python-exit-code 1 '..\character-hunyuan-v1\poster-right-bow-v56\Suzume_dual_scene_right_bow_v56.blend' --python 'tools\export_v56_assets.py'
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --python-exit-code 1 --python 'tools\export_character_asset.py'
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --threads 4 --python-exit-code 1 --python 'tools\validate_assets.py'
python tools\make_xcode_project.py
python tools\build_preview.py
node tools\verify_preview.cjs
```

前两步使用 Blender 5 自带的 bpy 和 OpenUSD。最后一步需要 Node.js、Playwright 和脚本中指定的 Chrome 路径。Swift/Xcode 构建是单独的 Mac 阶段。

重导出脚本按原仓库目录运行，需要原始 v56 和已有 Three.js 依赖；交付压缩包不重复包含大型源 blend。打开现成 HTML 或在 Mac 构建已有 Xcode 工程不需要这些源依赖。

`export_v56_assets.py` 在源“Night meadow through the door”场景提取花海，在“Official poster courtyard v38”提取门洞与门框。每次取源对象世界矩阵前显式激活对应场景、更新依赖图，避免跨场景读取陈旧父级矩阵，把地面导出成竖直面。

Blender 5 可直接输出 `.usdz`，本流程不需要 Reality Converter。导出开启 USD Preview Surface、贴图打包、米制与 Y-up 转换；不导出相机、源灯光、骨架、体积节点或 MaterialX。

`validate_assets.py` 使用 `UsdUtils.ComplianceChecker(arkit=True)`；同时检查未解析的纹理引用、64 字节包对齐、单位、地面轴向和源文件哈希。验证后从**已交付的 USDZ**回读，再导出 GLB 供桌面预览使用。

## 天空缓存

`NightSky.png` 与 `validation/sky_clean_v2.json` 构成当前天空缓存。源天空或源文件变化后，移走这两个文件再导出，以重新烘焙。改变门洞、地形或植物时也应重新运行完整验证。

## 工程生成

`export_character_asset.py` 把合成 GLB 规范化到脚底中心、1.62 m、Y-up，并将六张源 4K 贴图缩至 2K 后重新打包为 `Character.usdz`。

`make_xcode_project.py` 生成原生 `.xcodeproj`、共享 scheme 与 Info.plist，包含 7 个 Swift 文件和 6 个运行资源，不依赖安装 XcodeGen。`project.yml` 仍作为可选的 XcodeGen 描述保留。

工程生成成功只是文件结构就绪，不代表 Swift 编译通过。Mac 上使用 `VisionProPortal/build-on-mac.sh` 执行实际模拟器构建。
