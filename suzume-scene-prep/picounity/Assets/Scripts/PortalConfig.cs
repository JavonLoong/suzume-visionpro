using UnityEngine;

/// <summary>
/// 铃芽之旅 · 梦幻门（Unity / PICO 4 Ultra 版）全局配置与校准参数。
/// 与 Vision Pro 版（AssetManifest.json & PortalConfig.swift）及 v32/v56 原生场景保持严格一致的归一化坐标与比例：
/// - 原点：门槛地面中心 (0, 0, 0)
/// - 坐标轴：+Y 向上，从门外 (+Z) 朝门内 (-Z) 观看（Unity 左手系下屏幕右侧为 -X，屏幕左侧为 +X）
/// - 基准门洞净高：2.10 m，基准门洞净宽：0.878918 m（保留 v56 源场景 1.423 × 3.400 原比例，缩放系数 2.1/3.4 = 0.617647）
/// - 门扇铰链轴心（Animated door leaf and hinges）：位于右侧门框立柱 (X = -0.4372834m, Z = +0.0339706m)，绕 +Y 轴旋转 88.8° (1.55 rad) 向门内打开。
/// </summary>
public static class PortalConfig
{
    public enum FrameMode
    {
        Reference = 0,  // 显示对齐门框（带白漆剥落与常春藤贴图的真实门框）
        Occlusion = 1,  // 门框仅作遮挡（透视模式下由实体门框显示外观，虚拟门框只写深度与 Stencil 遮挡）
        Hidden = 2      // 隐藏虚拟门框
    }

    // ---- 门洞净开口（与 VisionPro AssetManifest.json 严格一致，单位：米）----
    public const float BaseDoorWidth = 0.87891794f;
    public const float BaseDoorHeight = 2.10f;
    public const float DoorWidth = BaseDoorWidth;
    public const float DoorHeight = BaseDoorHeight;
    public const float OpeningCenterY = BaseDoorHeight * 0.5f; // 1.05 m
    public const float DoorThickness = 0.18f;

    // ---- v32/v56 真实门扇铰链与门把手归一化坐标（单位：米）----
    // 源场景 hinge location=(-0.804, 0.240, 0.055), parentScale.x=-0.880575, uniformScale=2.1/3.4=0.617647
    public const float DoorHingeX = -0.4372834f;
    public const float DoorHingeZ = 0.0339706f;
    public const float MovieDoorOpenRadians = 1.55f;
    public const float MovieDoorOpenAngle = 88.808f; // 1.55 rad 对应的角度
    public static readonly Vector3 DoorKnobLocalPos = new Vector3(0.4125f, 0.955f, 0.1334f);

    // ---- 门在现实空间中的放置（实机校准项）----
    public static Vector3 PortalPosition = new Vector3(0f, 0f, 0f);
    public static float PortalRotationY = 0f;
    public static float WorldScale = 1f;
    public static float LightMultiplier = 1.18f;
    public static float AtmosphereIntensity = 1.38f;
    public static float WindStrength = 1.0f;

    // ---- 真实资产路径（从 VisionPro 验证通过的 USDZ 导出的 FBX 模型与烘焙贴图）----
    public const string DoorFrameAssetPath = "Assets/Models/DoorFrame.fbx";
    public const string DoorLeafAssetPath = "Assets/Models/DoorLeaf.fbx";
    public const string DreamWorldAssetPath = "Assets/Models/DreamWorld.fbx";
    public const string CharacterAssetPath = "Assets/Models/Character.fbx";
    public const string DoorAssetPath = DoorFrameAssetPath;

    // ---- 门后梦幻世界与角色配置 ----
    public const bool UseRealDreamWorld = true;
    public const bool UseRealDoor = true;
    public const bool UseCharacter = true;
    public const bool EnableStars = true;
    public const bool EnableWater = true;
    public const bool EnableFlowerField = true;

    // 梦幻世界已按门槛中心 (0,0,0) 归一化，配合 PortalTarget.shader 的门洞平面裁剪（_ClipPlane），无需后推 200 米
    public static Vector3 DreamWorldOffset = Vector3.zero;
    public static float DreamWorldScale = 1f;

    // 铃芽角色两种标准位置：
    // 1) 花海远眺模式：站在门后 2.7 米花海中，背对门洞望向远方星空花海
    public static Vector3 CharacterOffset = new Vector3(0f, 0f, -2.7f);
    public static float CharacterYaw = 180f;
    // 2) 电影门槛推门模式（v32/v37）：站在门洞中左位置，右手向右侧伸出握持旋转门扇上的黄铜门把（不与门板穿插）
    public static Vector3 CharacterDoorPushOffset = new Vector3(0.08f, 0f, -0.52f);
    public static float CharacterDoorPushYaw = 162f;

    // ---- 门框与门扇模式 ----
    public static FrameMode DefaultFrameMode = FrameMode.Reference;
    public const bool DefaultShowDoorLeaf = true;
    public const float DoorOpenAngle = MovieDoorOpenAngle;

    // ---- 默认观察相机（与 Vision Pro 离线预览 portal-front.png 对齐）----
    public static Vector3 DefaultCameraPosition = new Vector3(0f, 1.60f, 3.20f);
    public static Vector3 DefaultCameraTarget = new Vector3(0f, 1.05f, 0f);
    public const float DefaultCameraFov = 49f;

    // ---- 编辑器预览 ----
    public const bool BuildInEditMode = true;
    public const bool DisableStencilInEditMode = false;
    public static Color PreviewWallColor = new Color(0.10f, 0.13f, 0.12f);

    // ---- 空间音频 ----
    public const bool EnableSpatialAudio = false;
}
