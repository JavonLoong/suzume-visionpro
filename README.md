# 铃芽之旅 · Apple Vision Pro 适配

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
| 每个文件的位置、大小、SHA-256 | [PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) |
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
