> 历史草案：此文保留 Cursor 初始方案，部分占位描述和 API 示例已被后续工程替换。当前代码、资源和验证状态见[仓库首页](../../README.md)。

# 铃芽之旅 · 梦幻门（visionOS 门户体验）

把「实体白门」和「门后梦幻世界」结合起来的 Apple Vision Pro 应用：戴上眼镜，透过真实门洞看到门后的星空 / 花海 / 水面世界，门外保持现实透视。

> 重要：visionOS 应用只能在 **macOS + Xcode 16+** 上构建，并在 **Vision Pro 真机（或 Vision Pro 模拟器）** 上运行。本仓库提供完整 Swift 源码、技术方案和 USDZ 导出流程，但**无法在 Windows 上编译、上机**。

## 一、文件清单

```
visionpro/
├── 技术方案.md                  # 需求 → 实现方案（对齐/遮挡/视差）
├── USDZ导出流程.md              # 把 .blend 场景导出成 RealityKit 资产
├── README.md                    # 本文件
└── VisionProPortal/
    └── VisionProPortal/
        ├── VisionProPortalApp.swift    # @main 入口
        ├── ContentView.swift           # 主窗口（进入/退出）
        ├── PortalImmersiveView.swift   # 沉浸空间视图
        ├── PortalSystem.swift          # PortalComponent 核心组装
        ├── DreamWorldBuilder.swift     # 门后梦幻世界（星空/水面/花海）
        ├── DoorOcclusion.swift         # 虚拟门框+门扇（遮挡兜底）
        └── PortalConfig.swift          # 所有可调参数（实机只改这里）
```

## 二、在 Mac 上组装（两种方式任选）

### 方式 A：XcodeGen（推荐，一键生成工程）

1. 安装 XcodeGen：`brew install xcodegen`
2. 在本目录运行：`xcodegen generate`
3. 双击生成的 `VisionProPortal.xcodeproj` 打开。

（`project.yml` 已写好，见仓库根；若你没装 XcodeGen，用方式 B。）

### 方式 B：Xcode 手动新建（最稳）

1. Xcode → File → New → Project → **visionOS → App**。
2. 模板选 **Immersive Space**（或 Window），语言 Swift，命名 `VisionProPortal`。
3. 用本仓库 `VisionProPortal/` 下的同名 `.swift` 文件**覆盖**模板生成的同名文件（App、ContentView、ImmersiveView）。
4. 把 `PortalSystem.swift`、`DreamWorldBuilder.swift`、`DoorOcclusion.swift`、`PortalConfig.swift` **拖进** Xcode 项目（勾选 Copy items if needed）。
5. 若模板没有 `ImmersiveSpace(id:)`，按 `VisionProPortalApp.swift` 里的写法补上 `ImmersiveSpace` 和 `.immersionStyle(.mixed)`。

## 三、运行

1. 选择运行目标：`Apple Vision Pro`（真机）或 `Vision Pro Simulator`（模拟器，无需设备）。
2. 点 Run。
3. 主窗口点「进入梦幻门」，即进入混合沉浸空间。
4. 透过门洞应看到门后的星空 / 花海 / 水面；门外是现实（模拟器里是虚拟环境）。

## 四、替换成真正的建模资产（USDZ）

当前梦幻世界是程序化几何（占位）。要接入现有铃芽建模：

1. 按 `USDZ导出流程.md`，把门后梦幻世界导出成 `DreamWorld.usdz`，把白门/门扇导出成 `SuzumeDoor.usdz`。
2. 把 `.usdz` 放进 `VisionProPortal/VisionProPortal/Resources/`（或 RealityKitContent 包）。
3. 在 `DreamWorldBuilder.build()` 里，把 `makeStarField()/makeWater()/makeFlowerField()` 换成：
   ```swift
   if let asset = try? await Entity.load(named: "DreamWorld") {
       world.addChild(asset)
   }
   ```
4. 在 `DoorOcclusion.makeDoorAssembly()` 里，把程序化门框/门扇换成加载 `SuzumeDoor.usdz`。

## 五、实机校准（必须戴真机做）

1. 打开 app，进入沉浸空间。
2. 改 `PortalConfig.swift` 里的 `portalPosition` / `portalRotationY` / `doorWidth` / `doorHeight`，把虚拟门洞四角对齐到实体门框四角。
3. 确认：转头、左右移动、靠近时，门后世界有正确视差且稳定留在门框内。
4. 若门扇/人会穿帮，按 `技术方案.md` 第 5 节逐步升级遮挡方案（虚拟门扇 → Scene Reconstruction → OcclusionMaterial）。

## 六、已知边界（诚实说明）

- 本仓库代码**未经过编译验证**（Windows 无 Xcode）。首次构建如遇 API 名称差异（不同 Xcode/RealityKit 版本），按编译器提示微调即可。
- 「实体门对齐」「真人遮挡虚拟世界」**必须在实机验证**，无法在代码里保证。
- 需求文档里「门扇能否活动、是否允许跨门进入、用电影哪一幕、是否多人观看」均为**待确认项**，本代码默认：门扇关闭、只门外观看、单人。
