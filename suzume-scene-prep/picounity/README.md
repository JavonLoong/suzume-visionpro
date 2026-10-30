# 铃芽之旅 · 梦幻门（Unity / PICO 4 Ultra 版）

把「实体白门」和「门后梦幻世界」结合的 MR 体验：戴上 PICO 4 Ultra（或在桌面 Play 模式预览），透过门洞看到门后的暮光星空、2500 朵立体花海、5000 簇草叶与门后 2.7 米处望向远方的铃芽角色；门外保持现实环境透视（Passthrough）。

> 本机（Windows 11）已装好 Unity 2022.3.62f3 + Android Build Support，已接入与 Apple Vision Pro 版**完全同源的四份归一化三维模型与 12 张烘焙/PBR 贴图**，并通过三视角渲染与 Play 模式运行时验证。

---

## 一、核心渲染与裁剪原理（对齐 Vision Pro `PortalComponent`）

1. **门洞模板遮罩**（`Assets/Shaders/PortalMask.shader`，`Queue = Geometry-50`）：
   - 在门洞净开口（基准 `0.8789 m × 2.10 m`，门槛地面中心为 `(0, 0, 0)`）写入模板缓冲 `Stencil = 1`，本身不写颜色与深度。
2. **实体门框遮挡模式**（`Assets/Shaders/DoorOcclusion.shader`，`Queue = Geometry-40`）：
   - 当切换为「门框仅作遮挡」模式时，虚拟门框不输出任何颜色（透视画面直接露出真实世界的实体门框），但写入深度并将门框区域的 `Stencil` 重置为 `0`，确保侧面观看时门框厚度能真实遮挡门内花海。
3. **门后世界与门洞平面裁剪**（`Assets/Shaders/PortalTarget.shader`，`Queue = Geometry+10`）：
   - 仅在 `Stencil == 1` 区域渲染门后花海与铃芽角色；
   - 内置世界空间门洞平面裁剪（`_ClipPlane`），自动裁掉位于门洞平面观察者一侧（$z > 0$）的近景地形与天空半球，**无需把梦幻世界往后推 200 米**，让花草从门槛后方 0.07 米处自然铺展；
   - 内置暮光半球环境光 + 月光漫反射照明与亮度倍率调节（`_LightMultiplier`）。
4. **对齐参考门框**（`Assets/Shaders/DoorFrame.shader`，`Queue = Geometry+20`）：
   - 还原白漆剥落与常春藤攀爬的原始 UV 贴图，供实机对齐实体门框四角或桌面预览。

---

## 二、已接入的真实资产清单（与 Vision Pro 版 1:1 同源）

| 资产 | 路径 | 规格与内容 |
|---|---|---|
| 门后梦幻花海世界 | `Assets/Models/DreamWorld.fbx` | 378,100 三角面：烘焙暮光夜空穹顶、近/远景起伏草原、**2,500 朵独立花朵**、**2,500 根花茎**、**5,000 簇草叶**、立体发光星辰 |
| 混元四视图轻量铃芽角色 | `Assets/Models/Character.fbx` | 91,573 三角面：身高 1.62 m，站在门后 `2.7 m` 处背对门洞望向花海，含身体/头部 2K PBR 与法线贴图 |
| 实体比例白门框 | `Assets/Models/DoorFrame.fbx` | 964 三角面：6 子网格，带剥落白漆与常春藤贴图 |
| 独立可开合门扇 | `Assets/Models/DoorLeaf.fbx` | 3,372 三角面：7 子网格，挂在左铰链可自由调节开合角度（`0° ~ 120°`） |
| 烘焙与 PBR 贴图（12 张） | `Assets/Textures/` & `Assets/Resources/Textures/` | `NightSky.png` (2048×1024)、`NearMeadow_BaseColor.png` (2048²)、`DistantMeadow_BaseColor.png` (1024²)、`FlowerPalette.png` (Point 采样调色板)、门框贴图 ×2、角色 PBR 贴图 ×6 |

---

## 三、交互预览与实机校准面板（`PortalCalibrationUI.cs`）

打开 `Assets/Scenes/SuzumePortal.unity` 点击 **Play**（或执行菜单 `Tools → 搭建梦幻门场景 (Suzume Portal)`），画面右侧自带实时交互与校准面板（按 `Tab` 或 `H` 键可随时隐藏/显示面板）：

- **一、透过门洞 · 移动视角**：
  - 鼠标左键拖拽画面或拖动滑块调节 **左右移动**（`-1.6 ~ +1.6 m`）、**眼睛高度**（`0.6 ~ 2.4 m`）、滚轮调节 **距门距离**（`0.65 ~ 6.0 m`）；
  - 一键切换 **「回到门前」** 与 **「查看完整花海」**（360° 全景检查花海与铃芽角色）。
- **二、对齐实体门（MR 实机校准）**：
  - **门洞净高**（`0.5 ~ 3.5 m`，默认 `2.10 m`，净宽与花海世界按 `v56` 原比例自动同步缩放）；
  - **花海亮度**（`0.3x ~ 2.5x`）、**门体朝向**（`-180° ~ +180°`）；
  - **虚拟门框三模式切换**：`显示对齐门框` / `门框仅作遮挡` / `隐藏门框`；
  - **门后铃芽角色开关**、**可活动门扇开关与开门角度滑块**；
  - **保存参数 / 读取参数 / 重置**（持久化至 `PlayerPrefs`）。

---

## 四、验证渲染输出（`preview/`）

- `preview/unity-portal-front.png`：正面透过门洞看铃芽背影、花海与暮光云（1440×900）
- `preview/unity-portal-side.png`：侧面移动视角看门洞三维视差与门框遮挡（1440×900）
- `preview/unity-world-full.png`：完整花海与铃芽角色全景检查（1440×900）
- `preview/unity-playmode-运行时.png`：Play 模式运行时实测截图（1440×900）
