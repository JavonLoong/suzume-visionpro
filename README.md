# 铃芽之旅 · Pico / Unity / Vision Pro 完整项目

这里是项目的统一协作入口，包含 Pico / Unity 源码、场景、模型、贴图、Vision Pro 工程、场景制作脚本，以及 Blender 和打印资料的下载索引。

**2026-11-24 最新更新：PICO 1.13.0（11.18 版，待头显实测）。** [下载 APK](https://github.com/JavonLoong/suzume-visionpro/releases/download/project-update-2026-11-24/SuzumePortal-PICO-v1.13.0.apk) · [本次发布说明](docs/PICO-v1.13.0-project-update.md) · [最新模型与制作资料](https://github.com/JavonLoong/suzume-visionpro/releases/tag/project-update-2026-11-24)。加入识别结果按键固定、整体和四角前后左右上下调整、保存与取消；后台识别和位置求解继续优化。电脑回归与打包已完成，最新包尚未进行头显现场验证。同步更新九块底座、500 毫米底座和内藏轴试配资料，具体试制状态见说明。

以下为历史版本记录。

**2026-11-18 更新：PICO v1.12（versionCode 13）。** [直接下载 APK](https://github.com/JavonLoong/suzume-visionpro/releases/download/pico-v1.12-door-vision-2026-11-18/SuzumePortal-PICO-v1.12.apk) · [完整发布记录](docs/PICO-v1.12-door-vision.md)。应用已加入从相机画面识别实体小门的自动定位流程，不要求给门增加标记或配件；检测模型、训练与评估代码、最终权重、Unity 推理和手动四点兜底均已入库。编辑器检查和 APK 构建已通过，但头显未连接，因此 PICO 4 Ultra 相机取图、图像方向、外参方向、真机速度与端到端自动定位仍未验证。

**上一版人工定位：** [PICO v1.11 发布记录](docs/PICO-v1.11.md)。该版用手柄两次瞄准确定每个门角，已在真机完成一次连续四角定位，可在自动识别失败时继续作为兜底。

**继续开发 Pico：** 阅读 [协同开发说明](COLLABORATION.md)，按说明拉取官方 SDK 后，用 Unity **2022.3.62f3** 打开 [picounity](suzume-scene-prep/picounity/)。`Assets`、`.meta`、包清单和项目设置均已入库。

**直接试用或取完整制作资料：** 查看 [完整项目发布页](https://github.com/JavonLoong/suzume-visionpro/releases/tag/complete-project-2026-10-30) 和 [下载清单](DOWNLOADS.md)。大文件放在同一仓库的 Release；不会随普通 `git clone` 一起下载。每个文件的存放位置和 SHA-256 见 [本次文件清单](PROJECT_MANIFEST.json)。

**版本范围：** 这是一次有时间记录的项目快照。本机之后的修改需要提交和推送才会出现在 GitHub；具体安装包版本与检查结果以对应 Release 说明为准。`PUBLICATION_MANIFEST.json` 保留 2026-10-11 历史归档记录。

| 要做的事 | 入口 |
| --- | --- |
| 修改 Pico 场景、门框定位和手柄交互 | [Pico / Unity 工程](suzume-scene-prep/picounity/) |
| 换电脑准备环境、多人合作 | [COLLABORATION.md](COLLABORATION.md) |
| 修改 Vision Pro 应用 | [VisionProPortal](suzume-scene-prep/visionpro/VisionProPortal/) |
| 取 Blender、打印模型、历史资料和 APK | [DOWNLOADS.md](DOWNLOADS.md) |

## Vision Pro 分支说明

将已有的铃芽之旅三维场景适配为 visionOS 门户体验：通过实体门洞观看门后的花海与星空，门洞之外保留现实透视。这个仓库同时保存建模脚本、历代场景、人物多视图资料和离线预览，方便继续开发。

**当前 v0.3 是可交给实验室 Mac 的开发快照，尚未经过 Xcode 编译或 Vision Pro 实测。** 花海、门框、门扇和轻量角色四份 USDZ 的结构校验已通过；门框定位、现实门扇和行人的遮挡、运行性能仍需后续验证。桌面网页预览不等于头显效果。

## 从这里开始

- **桌面检查 v57：** 下载 [v57 完整交付包](suzume-scene-prep/visionpro/铃芽之旅_VisionPro适配_v57.zip)，或直接打开 [单文件离线预览](suzume-scene-prep/visionpro/铃芽之旅_VisionPro适配_离线预览.html)。
- **继续 visionOS 开发：** 打开 [Xcode 工程](suzume-scene-prep/visionpro/VisionProPortal/VisionProPortal.xcodeproj)。工程已包含花海、门框、门扇、轻量角色 USDZ、天空纹理和尺寸清单。
- **继续 Blender 建模：** 下载 [v56 源模型包](https://github.com/JavonLoong/suzume-visionpro/releases/download/project-snapshot-2026-10-11/01-source-v56.zip)，包括原始命名版与中文版 `.blend`。
- **查看之前交付的场景：** 下载 [离线 HTML 合集](https://github.com/JavonLoong/suzume-visionpro/releases/download/project-snapshot-2026-10-11/02-offline-html.zip)，包含 v49、v38、v37 和全部场景整合页。

![v49 场景渲染](docs/previews/poster-front-v49.png)

## 工程与资料

| 内容 | 位置 |
| --- | --- |
| Swift / RealityKit 应用、Xcode 工程、构建脚本 | [VisionProPortal](suzume-scene-prep/visionpro/VisionProPortal/) |
| 模型导出、结构校验、工程生成工具 | [visionpro/tools](suzume-scene-prep/visionpro/tools/) |
| 已导出的 USDZ 和纹理 | [Resources](suzume-scene-prep/visionpro/VisionProPortal/VisionProPortal/Resources/) |
| GLB 预览模型 | [preview-assets](suzume-scene-prep/visionpro/preview-assets/) |
| 资产校验报告 | [asset_validation.json](suzume-scene-prep/visionpro/validation/asset_validation.json) |
| 实体园林与梦幻门的原始需求 | [体验需求](suzume-scene-prep/AppleVisionPro_实体园林与梦幻门_体验需求.txt) |
| 早期建模路线及参考来源 | [建模准备说明](suzume-scene-prep/建模准备说明.md) |
| 人物多视图、头模和历史建模代码 | [character-hunyuan-v1](suzume-scene-prep/character-hunyuan-v1/) |
| 2026-10-11 历史归档的位置、大小、SHA-256 | [PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) |
| 大文件下载与恢复 | [下载清单](DOWNLOADS.md) |

## 在 Mac 上编译

需要安装包含 visionOS SDK 的 Xcode；工程部署目标为 visionOS 2.0。仓库已包含生成的 `.xcodeproj`，无需先装 XcodeGen。

```bash
git clone https://github.com/JavonLoong/suzume-visionpro.git
cd suzume-visionpro/suzume-scene-prep/visionpro/VisionProPortal
bash build-on-mac.sh
```

该脚本构建模拟器版本，不安装到设备。也可直接用 Xcode 打开工程。真机运行时需要配置自己的开发团队与签名。

当前应用支持进入 / 退出混合沉浸空间、按比例调整门洞尺寸、手动调节位置和朝向、选择门框显示或遮挡模式。保存的位置是会话坐标参数，不是已实现的持久空间锚点。

门后世界保留地形、花草、星星和铃芽角色的三维几何；角色高 1.62 m、91,573 个三角面，位于门后 2.7 m。远处天空和云层采用烘焙纹理，低空体积雾没有纳入这版运行资产。门扇作为独立资源归档，不代表已完成现实门扇跟踪。

## 完整资产归档

代码、工程和当前适配资源在 Git 中；体量较大的 Blender 文件、几何中间数据、历史纹理及离线 HTML 在同仓库的 [Release](https://github.com/JavonLoong/suzume-visionpro/releases/tag/project-snapshot-2026-10-11) 中。

各 ZIP 都是独立压缩包，内部路径从 `suzume-scene-prep/` 开始，解压到仓库根目录即可恢复。历史脚本按版本保留，部分包含原来的本机路径；它们不是已经验证过的跨平台一键重建流程。

此快照归档了项目内容，排除了 `.blend1` 自动备份、日志、可重新安装的 Python 依赖、缓存、浏览器服务页面截图和 Blender 个人偏好文件。历代设计说明保留其原始时间与状态，当前进度以本页及具体校验报告为准。
