> 历史草案：此文保留 Cursor 初始方案，部分占位描述和 API 示例已被后续工程替换。当前代码、资源和验证状态见[仓库首页](../../README.md)。

# USDZ 导出流程 — 把铃芽建模转成 RealityKit 资产

RealityKit / visionOS 原生的 3D 资产格式是 **USDZ**（或 `Entity.load(named:)` 支持的 `.usdz` / `.usda`）。现有建模在 `suzume-scene-prep/character-hunyuan-v1/` 下，是 `.blend`（Blender）和 `.glb` 文件。下面是转成 USDZ 的三条路，按可靠性排序。

---

## 路线一：Blender 直接导出（推荐，本机可做）

Blender 4.x 原生支持 USD 导出。

1. 打开最新场景，例如门后梦幻世界：
   `character-hunyuan-v1/movie-night-v30/Suzume_scene_movie_night_v30.blend`
   或海报双场景：
   `character-hunyuan-v1/poster-right-bow-v56/Suzume_dual_scene_right_bow_v56.blend`
2. 确认要导出的对象（建议只导出「门后世界」，不含门外园林）：
   - 门后星空 / 花海 / 水面夜景部分；
   - 白门 + 门扇单独导出（供 `DoorOcclusion` 兜底）。
3. `File → Export → Universal Scene Description (.usdc/.usda)`。
   - 选 `.usda`（文本格式，便于检查）或 `.usdc`（二进制）。
   - 勾选 **Selection Only**（只导出选中对象）。
4. 导出得到 `DreamWorld.usda`、`SuzumeDoor.usda`。

**注意**：Blender 导出的 USD 通常不带 USDZ 打包（贴图可能外置）。如果模型贴图多，见路线三。

## 路线二：Reality Converter（macOS，最稳）

Apple 官方免费的 Reality Converter 能把 `.obj` / `.gltf` / `.usd` 等转成 `.usdz`，并正确打包贴图。

1. 在 Blender 里 `Export → glTF 2.0 (.glb)` 导出中间格式（贴图会内嵌）。
2. Mac 上打开 Reality Converter（App Store 下载），拖入 `.glb`。
3. 调整材质、尺寸、坐标，导出为 `.usdz`。

这是贴图最不容易丢的路线，但需要 Mac。

## 路线三：本机 Python + USD 工具链（进阶）

若必须全在 Windows 完成，可装 Pixar 官方 USD 的 Python 绑定（`usd-core` pip 包）和 `usdzip`：

```bash
pip install usd-core
```

然后：
1. 先由 Blender 导出 `.usda` / `.usdc`（路线一）。
2. 用 `usdzip` 把 `.usda` 与其依赖贴图打包成 `.usdz`：
   ```bash
   usdzip DreamWorld.usdz DreamWorld.usda
   ```

**局限**：`usd-core` 的 `usdzip` 打包命令、贴图解析对 Blender 导出的复杂材质支持有限，失败率高。优先路线一、二。

## 导出后的坐标与尺度核对（重要）

现有建模约定：**门槛中心为原点，Z 向上，门高 2.10 m（占位）**。而 RealityKit 默认坐标也是米制、Y 向上（或 visionOS 用 Z 向上）。导出后要核对：

1. **单位**：确认 USD 文件里 1 单位 = 1 米。Blender 导出时选 scale 1.0，别用 cm。
2. **朝向**：Blender 的 Z 向上 vs USD/RealityKit 的 Y 向上。导出时在 Blender 里把场景转成 Y 向上，或导出后在 USD 里加 `-Z→Y` 的旋转。
3. **门洞尺寸**：导出的门洞净开口要与 `PortalConfig.doorWidth/doorHeight` 一致；不一致就在 Blender 里量好再改 `PortalConfig`。

## 分件清单（对应需求「区分三类模型」）

| 用途 | 资产 | 说明 |
|---|---|---|
| 实体打印参考 | 白门、门框、砖基、园林构件 | 视觉模型 ≠ 可制造模型，打印前另做拆件/厚度/支撑 |
| 门后实时渲染 | 星空/花海/水面夜景 | 给 portal 的 target 世界，导出 USDZ |
| 对齐+遮挡兜底 | 门框净开口、门扇 | 简化对应模型，导出 USDZ 供 `DoorOcclusion` |

## 落地步骤小结

1. 本机：Blender 导出门后世界 + 白门 → `.usda`。
2. （可选）Mac Reality Converter → `.usdz`（贴图最稳）。
3. 把 `.usdz` 放进 `VisionProPortal/VisionProPortal/Resources/`。
4. 改 `DreamWorldBuilder.swift` / `DoorOcclusion.swift`，用 `Entity.load(named:)` 加载。
5. 在 Vision Pro 上核对坐标、尺度、门洞对齐。
