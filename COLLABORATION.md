# 协同开发

这个仓库统一保存铃芽之旅的 Pico / Unity、Vision Pro、场景制作脚本和资料索引。
源码、当前应用必需模型和贴图随 Git 提供。大型 Blender、打印文件和历史场景保存在同一仓库的 Releases，位置见 [DOWNLOADS.md](DOWNLOADS.md)。

如果还需要恢复本次快照的全部大型制作资料，使用 Python **3.9 或以上** 执行：

```shell
python tools/project_assets.py
python tools/project_assets.py --restore
python tools/project_assets.py --verify
```

第一条只列出下载项；第二条按清单下载、校验并恢复缺失文件；第三条核对本地文件是否与快照一致。
已有同名文件如果内容不同，脚本会停止，保留本地修改。可加 `--scope pico`、`--scope visionpro` 或 `--scope print` 缩小范围。
此工具只恢复 `PROJECT_MANIFEST.json` 中的本次文件；更早的全部历史版本按下载页另取。PICO 官方 SDK 仍由下面的准备脚本处理。

## 准备 Pico 工程

安装 Git、Python 3、Unity Hub，再安装 Unity **2022.3.62f3** 和该版本的 **Android Build Support / SDK & NDK Tools / OpenJDK**。

Windows 上建议把仓库放在纯英文路径，例如 `D:/Projects/suzume-visionpro`。本项目在中文路径下执行 Android 打包时遇到过工具限制；英文路径可避免这个已知问题。

```shell
git clone https://github.com/JavonLoong/suzume-visionpro.git
cd suzume-visionpro
python tools/prepare_pico.py
```

在 Unity Hub 中打开 `suzume-scene-prep/picounity`，主场景是 `Assets/Scenes/SuzumePortal.unity`。
`Assets`、`.meta`、`Packages/manifest.json`、`Packages/packages-lock.json` 和 `ProjectSettings` 都需要保留。

PICO Integration 3.4.0 通过 Git 子模块固定到 `c93a59bab88d337fe0d54140499712897cedbe52`。
`prepare_pico.py` 从 PICO 官方仓库取回依赖，并应用 `tools/pico-sdk.patch`，还原当前工程的程序集兼容修改及透视初始化、AlphaBlend 环境模式处理。
补丁同时去掉未安装的手势示例、Live Preview、AR Subsystems 和 Composition Layers 引用；脚本可以重复执行，已应用时不会再次修改。
PICO SDK 遵守其原有许可，本仓库通过官方来源引用它。

第一次打开会由 Unity 下载 `manifest.json` 中的包并生成 `Library`，需要联网。
不要把 `Library`、`Temp`、`Logs`、`UserSettings`、个人签名密钥或本机密码提交到仓库。

## 构建和试用

打开场景后，可通过 Unity 的 Android Build Settings 构建。项目已有 `Assets/Editor/BuildPicoApk.cs` 构建入口，输出为 `Builds/SuzumePortal-PICO.apk`。
使用这个入口前，检查它选择的 SDK / NDK / JDK 路径与本机 Unity 安装目录一致；早期辅助脚本可能仍含作者本机路径。

`Assets/Plugins/Android/arm64-v8a/libPortalPassthrough.so` 随源码提供；对应 C++ 源码和 OpenXR 头文件在 `Native~/PortalPassthrough/`。修改该插件后，先检查 `build.ps1` 的本机 NDK 路径并重新编译，再构建 APK。该插件保留提交的全部画面层，没有旧诊断版的定时隐藏画面控制。

当前安装包是 v1.11。构建及真机验证范围见 [发布记录](docs/PICO-v1.11.md)。使用 Unity 批处理执行 `StablePlacementTrialCheck.Run` 可复核射线计算、场景显示、八次选线、最终确认及第二角点后休眠恢复的流程。

APK 是给测试者安装的成品，源码用于继续开发。已发布安装包见 [Releases](https://github.com/JavonLoong/suzume-visionpro/releases)。
在头显开启 USB 调试并授权电脑后，可执行：

```shell
adb devices
adb -s YOUR_DEVICE_SERIAL install -r path/to/SuzumePortal-PICO.apk
```

安装前确认目标序列号。同包名覆盖安装通常保留应用数据；调试签名不同的安装包不能直接互相覆盖，不要为了安装而直接清空已有数据。

## 合作修改

每项修改使用独立分支，描述要改变的行为。完成后提交 Pull Request，说明修改内容、测试方法和没有验证的部分。
场景 `.unity`、预制体 `.prefab` 和对应 `.meta` 要一起提交；同一场景多人同时改时，先协调各自改动范围。
每个可试用版本发布对应 APK，并在 Release 中注明源码提交号，使测试者和开发者能对上同一个版本。

Vision Pro 工程及其独立构建要求见 [visionpro/README.md](suzume-scene-prep/visionpro/README.md)。
打印相关资料属于独立制作分支，放入归档不表示已经通过最终打印验收。
