using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using System.IO;

/// <summary>
/// 一键搭建「铃芽之旅 · 梦幻门」完整 Unity 场景（接入 VisionPro 同源 FBX 资产与烘焙贴图）：
/// 包含：DoorFrame.fbx、DoorLeaf.fbx、DreamWorld.fbx（含 2500 朵花 + 2500 花茎 + 5000 草叶 + 烘焙夜空与草地）、
/// 以及混元四视图轻量铃芽角色 Character.fbx（身高 1.62m，站在门后 2.7m 处）。
/// </summary>
public static class SceneBootstrap
{
    const string MaterialDir = "Assets/Materials";
    const string SceneDir = "Assets/Scenes";
    const string ScenePath = "Assets/Scenes/SuzumePortal.unity";

    [MenuItem("Tools/搭建梦幻门场景 (Suzume Portal)")]
    public static void BuildScene()
    {
        if (!Directory.Exists(MaterialDir)) Directory.CreateDirectory(MaterialDir);
        if (!Directory.Exists(SceneDir)) Directory.CreateDirectory(SceneDir);
        AssetDatabase.Refresh();

        Material maskMat = CreateOrLoadMaterial("PortalMask", "Suzume/PortalMask");
        Material targetMat = CreateOrLoadMaterial("PortalTarget", "Suzume/PortalTarget");
        CreateOrLoadMaterial("DoorFrame", "Suzume/DoorFrame");
        CreateOrLoadMaterial("DoorOcclusion", "Suzume/DoorOcclusion");

        // 加载四份真实资产
        GameObject doorFramePrefab = LoadAsset(PortalConfig.DoorFrameAssetPath);
        GameObject doorLeafPrefab = LoadAsset(PortalConfig.DoorLeafAssetPath);
        GameObject dreamPrefab = LoadAsset(PortalConfig.DreamWorldAssetPath);
        GameObject characterPrefab = LoadAsset(PortalConfig.CharacterAssetPath);

        Debug.Log($"[SceneBootstrap] 真实资产加载结果：门框={(doorFramePrefab != null ? "✓" : "✗")} "
                  + $"门扇={(doorLeafPrefab != null ? "✓" : "✗")} "
                  + $"梦幻花海={(dreamPrefab != null ? "✓" : "✗")} "
                  + $"铃芽角色={(characterPrefab != null ? "✓" : "✗")}");

        var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

        // 门户根对象
        var root = new GameObject("SuzumePortalRoot");
        root.transform.position = PortalConfig.PortalPosition;
        root.transform.rotation = Quaternion.Euler(0f, PortalConfig.PortalRotationY, 0f);

        var mgr = root.AddComponent<PortalManager>();
        mgr.portalMaskMaterial = maskMat;
        mgr.portalTargetMaterial = targetMat;
        mgr.doorPrefab = doorFramePrefab;
        mgr.doorLeafPrefab = doorLeafPrefab;
        mgr.dreamWorldPrefab = dreamPrefab;
        mgr.characterPrefab = characterPrefab;
        mgr.portalHeight = PortalConfig.BaseDoorHeight;
        mgr.portalPosition = PortalConfig.PortalPosition;
        mgr.portalYaw = PortalConfig.PortalRotationY;
        mgr.lightMultiplier = PortalConfig.LightMultiplier;
        mgr.frameMode = PortalConfig.DefaultFrameMode;
        mgr.showDoorLeaf = PortalConfig.DefaultShowDoorLeaf;
        mgr.doorOpenAngle = PortalConfig.DoorOpenAngle;
        mgr.showCharacter = PortalConfig.UseCharacter;
        mgr.buildVirtualDoor = doorFramePrefab == null;
        mgr.buildPreviewWall = false;
        mgr.showOutsideReferenceFloor = true;
        mgr.BuildPortal();

        // 运行时视角控制与校准 UI
        var ui = root.AddComponent<PortalCalibrationUI>();
        ui.portalManager = mgr;

        // PICO 4 Ultra 透视启用脚本
        root.AddComponent<PicoPassthroughSetup>();

        // 主相机：与 Vision Pro 离线预览 (portal-front.png) 完全对齐
        var cam = Camera.main;
        if (cam != null)
        {
            cam.transform.position = PortalConfig.DefaultCameraPosition;
            cam.transform.LookAt(PortalConfig.DefaultCameraTarget);
            cam.fieldOfView = PortalConfig.DefaultCameraFov;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.094f, 0.133f, 0.114f, 1f);
            cam.nearClipPlane = 0.03f;
            cam.farClipPlane = 1200f;
            ui.targetCamera = cam;
        }

        var sun = Object.FindObjectOfType<Light>();
        if (sun != null)
        {
            sun.type = LightType.Directional;
            sun.transform.rotation = Quaternion.Euler(42f, -145f, 0f);
            sun.intensity = 1.15f;
            sun.color = new Color(1.0f, 0.95f, 0.88f);
        }

        // 将主场景加入 Build Settings（方便直接打包 Android / Windows）
        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene(ScenePath, true)
        };

        EditorSceneManager.SaveScene(scene, ScenePath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log("[SceneBootstrap] 场景已生成并保存: " + ScenePath);
        if (!Application.isBatchMode)
        {
            EditorUtility.DisplayDialog("搭建完成",
                "场景已生成：" + ScenePath
                + "\n\n真实资产："
                + "\n- 门框：" + (doorFramePrefab != null ? "✓" : "✗")
                + "\n- 门扇：" + (doorLeafPrefab != null ? "✓" : "✗")
                + "\n- 梦幻花海：" + (dreamPrefab != null ? "✓" : "✗")
                + "\n- 铃芽角色：" + (characterPrefab != null ? "✓" : "✗")
                + "\n\n点击 Play 即可体验与校准。", "好");
        }
    }

    static GameObject LoadAsset(string path)
    {
        var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (go == null) Debug.LogWarning("[SceneBootstrap] 找不到资产: " + path);
        return go;
    }

    static Material CreateOrLoadMaterial(string name, string shaderName)
    {
        string path = MaterialDir + "/" + name + ".mat";
        var shader = Shader.Find(shaderName) ?? Shader.Find("Standard");
        var existing = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (existing != null)
        {
            existing.shader = shader;
            EditorUtility.SetDirty(existing);
            return existing;
        }
        var mat = new Material(shader);
        AssetDatabase.CreateAsset(mat, path);
        return mat;
    }
}
