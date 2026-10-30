using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using System.IO;
using System.Text;

/// <summary>
/// 自动化几何、材质、双空间刚性门轴旋转与 20 骨骼二连杆 IK 渲染验证。
/// </summary>
public static class PortalRenderTest
{
    const string PreviewDir = "D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity/preview";
    const string OutFrontPng = PreviewDir + "/unity-portal-front.png";
    const string OutSidePng = PreviewDir + "/unity-portal-side.png";
    const string OutFullPng = PreviewDir + "/unity-world-full.png";
    const string OutMovieDoorIkPng = PreviewDir + "/unity-movie-door-ik.png";
    const string OutLegacyPng = PreviewDir + "/unity-Play模式-真实资产.png";
    const string OutDiag = "D:/Unity/portal-render-diag.txt";

    public static void Run()
    {
        var sb = new StringBuilder();
        Application.SetStackTraceLogType(LogType.Log, StackTraceLogType.None);

        if (!Directory.Exists(PreviewDir)) Directory.CreateDirectory(PreviewDir);

        AssetDatabase.Refresh();

        // 1) 搭建场景
        SceneBootstrap.BuildScene();
        sb.AppendLine("场景搭建: OK (Assets/Scenes/SuzumePortal.unity)");

        var mgr = Object.FindObjectOfType<PortalManager>();
        sb.AppendLine("PortalManager 存在: " + (mgr != null));
        if (mgr == null)
        {
            File.WriteAllText(OutDiag, sb.ToString(), Encoding.UTF8);
            return;
        }

        mgr.EnsureBuilt();
        mgr.UpdatePortalState();

        // 2) 验证双空间刚性门轴旋转（对齐 verify_export_door_v32.py 的 5 角度不变量检查）
        sb.AppendLine("\n=== 双空间刚性门轴旋转验证 (v32 5-Angle Sweep) ===");
        if (mgr.DayDoorHinge != null && mgr.NightDoorHinge != null)
        {
            float[] sweepDegs = { 0f, 13.88f, 44.40f, 74.93f, 88.81f };
            foreach (float ang in sweepDegs)
            {
                mgr.doorOpenAngle = ang;
                mgr.UpdatePortalState();
                Matrix4x4 mDay = mgr.DayDoorHinge.localToWorldMatrix;
                Matrix4x4 mNight = mgr.NightDoorHinge.localToWorldMatrix;
                float matDiff = 0f;
                for (int i = 0; i < 16; i++) matDiff = Mathf.Max(matDiff, Mathf.Abs(mDay[i] - mNight[i]));
                Vector3 p0 = mDay.MultiplyPoint3x4(Vector3.zero);
                Vector3 pW = mDay.MultiplyPoint3x4(new Vector3(PortalConfig.BaseDoorWidth, 0f, 0f));
                float widthWorld = Vector3.Distance(p0, pW);
                Vector3 knobW = mgr.DoorKnobTarget != null ? mgr.DoorKnobTarget.position : Vector3.zero;
                sb.AppendLine($"  - angle={ang:F2}° | dayNightMatMaxDiff={matDiff:E2} | rigidSpan={widthWorld:F6}m | knobWorld=({knobW.x:F3},{knobW.y:F3},{knobW.z:F3})");
            }
        }

        // 3) 验证铃芽 20 骨骼绑定与 SkinnedMeshRenderer
        sb.AppendLine("\n=== 铃芽 20 骨骼系统 (SuzumeHunyuanRig) 诊断 ===");
        var rigCtrl = mgr.RigController;
        if (rigCtrl != null)
        {
            rigCtrl.EnsureBound();
            sb.AppendLine($"已绑定骨骼数量: {rigCtrl.BoundBoneCount} / {SuzumeRigController.RequiredBoneNames.Length}");
            foreach (var bName in SuzumeRigController.RequiredBoneNames)
            {
                var b = rigCtrl.GetBone(bName);
                sb.AppendLine($"  - Bone [{bName}]: {(b != null ? $"OK pos={b.position} localRot={b.localEulerAngles}" : "MISSING")}");
            }
        }

        // 4) 统计三角面与各子网格（含 MeshRenderer + SkinnedMeshRenderer）世界包围盒
        int totalTris = 0;
        sb.AppendLine("\n=== 场景网格与包围盒诊断 ===");
        foreach (var mf in mgr.GetComponentsInChildren<MeshFilter>(true))
        {
            var mesh = mf.sharedMesh;
            var mr = mf.GetComponent<MeshRenderer>();
            if (mesh == null || mr == null) continue;
            int tris = mesh.triangles.Length / 3;
            totalTris += tris;
            var b = mr.bounds;
            string matInfo = mr.sharedMaterial != null
                ? $"{mr.sharedMaterial.name} ({mr.sharedMaterial.shader.name})"
                : "NULL";
            sb.AppendLine($"  - [Mesh] {GetPath(mf.transform)} | verts={mesh.vertexCount} tris={tris} "
                          + $"bounds=({b.min.x:F2},{b.min.y:F2},{b.min.z:F2})->({b.max.x:F2},{b.max.y:F2},{b.max.z:F2}) | mat={matInfo}");
        }
        foreach (var smr in mgr.GetComponentsInChildren<SkinnedMeshRenderer>(true))
        {
            var mesh = smr.sharedMesh;
            if (mesh == null) continue;
            int tris = mesh.triangles.Length / 3;
            totalTris += tris;
            var b = smr.bounds;
            string matInfo = smr.sharedMaterial != null
                ? $"{smr.sharedMaterial.name} ({smr.sharedMaterial.shader.name})"
                : "NULL";
            sb.AppendLine($"  - [SkinnedMesh] {GetPath(smr.transform)} | bones={smr.bones.Length} verts={mesh.vertexCount} tris={tris} "
                          + $"bounds=({b.min.x:F2},{b.min.y:F2},{b.min.z:F2})->({b.max.x:F2},{b.max.y:F2},{b.max.z:F2}) | mat={matInfo}");
        }
        sb.AppendLine($"总三角面数: {totalTris}");

        var cam = Camera.main;
        if (cam == null)
        {
            var camGo = new GameObject("TestCam");
            cam = camGo.AddComponent<Camera>();
            camGo.tag = "MainCamera";
        }
        cam.fieldOfView = PortalConfig.DefaultCameraFov;
        cam.nearClipPlane = 0.03f;
        cam.farClipPlane = 1200f;
        cam.clearFlags = CameraClearFlags.SolidColor;

        int W = 1920, H = 1200;

        // 5.1) 渲染视角 1：正面门洞预览 (portal-front, 花海远眺模式 + 门扇开启 88.8°)
        mgr.fullMeadowView = false;
        mgr.frameMode = PortalConfig.FrameMode.Reference;
        mgr.showDoorLeaf = true;
        mgr.doorOpenAngle = PortalConfig.MovieDoorOpenAngle;
        mgr.characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;
        mgr.showOutsideReferenceFloor = true;
        mgr.UpdatePortalState();

        cam.backgroundColor = new Color(0.094f, 0.133f, 0.114f, 1f);
        cam.transform.position = new Vector3(0f, 1.60f, 3.20f);
        cam.transform.LookAt(new Vector3(0f, 1.05f, 0f));
        var texFront = RenderToFile(cam, W, H, OutFrontPng);
        File.Copy(OutFrontPng, OutLegacyPng, true);
        sb.AppendLine($"\n[1] 正面门洞预览已输出: {OutFrontPng}");
        SamplePortalMetrics(texFront, sb, W, H, "正面门洞");

        // 5.2) 渲染视角 2：侧面视差预览 (portal-side, 检验双空间门扇在门洞边界的无缝裁剪)
        cam.transform.position = new Vector3(-0.85f, 1.60f, 2.85f);
        cam.transform.LookAt(new Vector3(0f, 1.05f, 0f));
        var texSide = RenderToFile(cam, W, H, OutSidePng);
        sb.AppendLine($"\n[2] 侧面视差预览已输出: {OutSidePng}");

        // 5.3) 渲染视角 3：电影门槛推门 IK 联动预览 (unity-movie-door-ik.png)
        mgr.characterPoseMode = SuzumeRigController.PoseMode.MovieDoorOpening;
        mgr.doorOpenAngle = 78f;
        mgr.UpdatePortalState();
        cam.transform.position = new Vector3(0.22f, 1.42f, 2.25f);
        cam.transform.LookAt(new Vector3(0.0f, 1.02f, -0.45f));
        var texIk = RenderToFile(cam, W, H, OutMovieDoorIkPng);
        sb.AppendLine($"\n[3] 电影推门二连杆 IK 预览已输出: {OutMovieDoorIkPng}");

        // 5.4) 渲染视角 4：完整花海与铃芽角色检查 (world-full)
        mgr.characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;
        mgr.doorOpenAngle = PortalConfig.MovieDoorOpenAngle;
        mgr.fullMeadowView = true;
        mgr.UpdatePortalState();
        cam.backgroundColor = new Color(0.031f, 0.039f, 0.114f, 1f);
        cam.transform.position = new Vector3(-1.30f, 1.70f, 2.50f);
        cam.transform.LookAt(new Vector3(0f, 0.80f, -8.0f));
        var texFull = RenderToFile(cam, W, H, OutFullPng);
        sb.AppendLine($"\n[4] 完整花海预览已输出: {OutFullPng}");

        // 恢复默认门洞状态并保存场景
        mgr.fullMeadowView = false;
        mgr.characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;
        mgr.doorOpenAngle = PortalConfig.MovieDoorOpenAngle;
        mgr.UpdatePortalState();
        cam.backgroundColor = new Color(0.094f, 0.133f, 0.114f, 1f);
        cam.transform.position = PortalConfig.DefaultCameraPosition;
        cam.transform.LookAt(PortalConfig.DefaultCameraTarget);

        Object.DestroyImmediate(texFront);
        Object.DestroyImmediate(texSide);
        Object.DestroyImmediate(texIk);
        Object.DestroyImmediate(texFull);

        EditorSceneManager.SaveOpenScenes();
        File.WriteAllText(OutDiag, sb.ToString(), Encoding.UTF8);
        Debug.Log("[PortalRenderTest]\n" + sb);
    }

    static Texture2D RenderToFile(Camera cam, int W, int H, string path)
    {
        var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 8;
        rt.Create();
        cam.targetTexture = rt;
        cam.Render();

        RenderTexture.active = rt;
        var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, W, H), 0, 0);
        tex.Apply();
        RenderTexture.active = null;
        cam.targetTexture = null;
        rt.Release();
        Object.DestroyImmediate(rt);

        File.WriteAllBytes(path, tex.EncodeToPNG());
        return tex;
    }

    static void SamplePortalMetrics(Texture2D tex, StringBuilder sb, int W, int H, string prefix)
    {
        int cx = W / 2;
        int cy = H / 2;
        Color centerCol = tex.GetPixel(cx, cy);
        Color skyCol = tex.GetPixel(cx, Mathf.RoundToInt(H * 0.66f));
        Color meadowCol = tex.GetPixel(cx, Mathf.RoundToInt(H * 0.34f));
        Color outsideCol = tex.GetPixel(Mathf.RoundToInt(W * 0.12f), Mathf.RoundToInt(H * 0.72f));
        sb.AppendLine($"  [{prefix}采样] 门心={centerCol} | 门内夜空={skyCol} | 门内花海={meadowCol} | 门外背景={outsideCol}");
    }

    static string GetPath(Transform t)
    {
        string p = t.name;
        while (t.parent != null)
        {
            t = t.parent;
            p = t.name + "/" + p;
        }
        return p;
    }
}
