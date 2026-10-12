# 铃芽之旅 · Apple Vision Pro 适配 v0.3

基于 v56 的门框、门扇和花海已经转换为 USDZ；混元 3D 四视图角色也已做成独立轻量 USDZ，并作为 `WorldComponent` 的子实体放在门后 2.7 米处。实验室已有 Mac 和 Vision Pro，下一阶段可以直接进入 Xcode 构建与实机校准。**当前 Windows 交付尚未声称已通过 Xcode 编译或头显验收。**

## 现在可以查看

- 双击 `铃芽之旅_VisionPro适配_离线预览.html`：独立文件，无需端口、服务器或联网。可以左右移动、调整观察高度与距离、查看完整花海。
- 预览使用交付 USDZ 回读得到的几何，门外网格仅代表现实空间。这是桌面几何预览，不是 visionOS 模拟器。
- `validation/portal-front.png`、`portal-side.png`、`world-full.png`：已检查的画面。

## 交付内容

| 文件 | 用途 |
| --- | --- |
| `VisionProPortal/VisionProPortal.xcodeproj` | 可交给 Mac 上 Xcode 打开的原生工程 |
| `VisionProPortal/VisionProPortal/*.swift` | RealityKit 门户、加载、校准与状态处理源码 |
| `Resources/DreamWorld.usdz` | v56 花海、地形、三维星点、远景天空；378,100 个三角面 |
| `Resources/DoorFrame.usdz` | 原比例门框；964 个三角面 |
| `Resources/DoorLeaf.usdz` | 独立门扇；3,372 个三角面；当前应用不自动显示或跟踪门扇 |
| `Resources/Character.usdz` | 混元四视图合成的轻量铃芽角色；91,573 个三角面；1.62 m；22.3 MB |
| `Resources/NightSky.png` | 从源场景烘焙的远景天空与环境照明输入 |
| `Resources/AssetManifest.json` | 源文件哈希、尺寸、导出数量与简化记录 |
| `validation/asset_validation.json` | USDZ 包、坐标、资源引用和合规检查结果 |

表中 `Resources` 位于 `VisionProPortal/VisionProPortal/Resources`。

## 已做的适配

1. 使用 `PortalMaterial + PortalComponent + WorldComponent`，门后世界加入实际实体树。门洞局部原点与模型统一为门槛中点，避免平面中心与模型底部错位。
2. 模型统一为米、Y 向上、朝 -Z 看入门内。源净开口约 1.42301 × 3.40；默认净高缩放至 2.10 m，净宽为 0.878918 m。宽、高与世界一起等比缩放。
3. 真实几何导出为移动端候选版本：2,500 朵花、对应的 2,500 根花茎与 5,000 组草，按固定种子选择并优先保留近处细节。原始 v56 未改动。
4. Cycles 的程序天空与远景体积云转换为可移植纹理；近处地形、花草和星点仍是几何。草地颜色烘焙到纹理；门框门扇采用源 UV 贴图和基础 PBR 材质。材质效果不等同于原 Cycles 渲染。
5. 混元 3D 生成分成两档：191.65 万三角面的 Blender 近景母版，以及 91,573 三角面的 Vision Pro 角色。实机资产把贴图降至 2K，USDZ 从 55.7 MB 降至 22.3 MB。
6. 角色属于门后 `WorldComponent`，和花海使用同一 IBL，只通过门户显示；离线门洞预览也使用同一份交付 USDZ 回读几何。
7. 主界面中文，加入位置、门槛高度、朝向、净高、照明调节，以及显示门框／仅遮挡／隐藏门框三种模式。
8. 异步加载显示真实错误；进入沉浸空间区分成功、取消与失败；离开时清理实体。参数可保存，但保存参数不是持久空间锚点。

## 已验证与待验证

已通过四份 USDZ 的 OpenUSD ARKit 合规检查，错误、失败项和警告均为 0；验证了贴图解析、单位、Y 轴朝向、地形水平、角色 1.62 m 身高、角色三角面预算以及 USDZ 压缩包格式。离线 HTML 在复制到独立目录并断网的 Chrome 中通过加载与视角切换检查，无 HTTP 请求或浏览器错误。源 v56 SHA-256 与导出前一致。

尚待 Mac/头显验证：Swift 类型检查与 Xcode 构建、RealityKit 实际材质、系统遮挡行为、头部视差、性能与稳定定位。本地几何检查不替代这些验证。

尚未开发：实体门识别、自动对齐、跨会话世界锚点、活动门扇或真实行人自动遮挡、多人同步，以及人跨门后切换整片沉浸世界。当前方案只针对已确认的“从实体门洞看另一个三维世界”。

## 以后有 Mac 时

1. 安装带 visionOS SDK 的 Xcode 16 或更新版本；项目最低目标 visionOS 2.0。
2. 打开 `VisionProPortal/VisionProPortal.xcodeproj`。无需先安装 XcodeGen。
3. 或在工程目录执行 `bash build-on-mac.sh`，脚本进行无需签名的模拟器构建，结果保存到 `BuildLogs/simulator-build.log`。
4. 模拟器构建通过后，再配置个人开发者签名和头显进行测试。对齐时先显示门框，将四个内角与实体门重合，再选“门框仅作遮挡”。

初次进入位置为当前沉浸空间原点前方 2 m。重新进入、系统重新定位或改变实体安装位置后，需要重新核对门洞；本版本不声称具备永久定位。

## 继续开发

见 `技术方案.md`、`USDZ导出流程.md` 和 `续接记录.md`。旧 Cursor 原型保留在 `cursor-original-source-20261011.zip`。

官方依据：[RealityKit PortalComponent](https://developer.apple.com/documentation/realitykit/portalcomponent)、[WorldComponent](https://developer.apple.com/documentation/realitykit/worldcomponent)、[PortalMaterial](https://developer.apple.com/documentation/realitykit/portalmaterial)。
