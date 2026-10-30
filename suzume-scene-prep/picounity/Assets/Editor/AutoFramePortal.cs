using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using System.Reflection;

/// <summary>
/// 编辑器加载 / 打开场景时：
/// 1. 自动开启最高画质（Ultra + 8x MSAA + 16x 各向异性过滤 + 零贴图降采样）；
/// 2. 自动把 Scene 视图对准门户并开启实时刷新；
/// 3. 进入 Play 模式时自动将 Game 视图最大化并锁定 1.0x 原生高清分辨率，彻底消除小窗缩放模糊。
/// </summary>
[InitializeOnLoad]
public static class AutoFramePortal
{
    const string SessionKey = "SuzumePortal.AutoFramed";
    const string AutoPlayKey = "SuzumePortal.AutoEnteredPlay";
    static int _attempts;

    static AutoFramePortal()
    {
        _attempts = 0;
        EditorApplication.update += Tick;
        EditorSceneManager.sceneOpened += OnSceneOpened;
        EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
    }

    [MenuItem("Tools/立即运行动态体验 (Play Suzume Portal)")]
    public static void StartDynamicExperience()
    {
        ApplyUltraQuality();
        MaximizeAndCrispGameView(true);
        if (!EditorApplication.isPlaying)
        {
            EditorApplication.EnterPlaymode();
        }
    }

    static void ApplyUltraQuality()
    {
        int ultraIdx = QualitySettings.names.Length - 1;
        if (ultraIdx >= 0 && QualitySettings.GetQualityLevel() != ultraIdx)
        {
            QualitySettings.SetQualityLevel(ultraIdx, true);
        }
        QualitySettings.globalTextureMipmapLimit = 0;
        QualitySettings.anisotropicFiltering = AnisotropicFiltering.ForceEnable;
        QualitySettings.antiAliasing = 8;
        Application.runInBackground = true;
    }

    static void MaximizeAndCrispGameView(bool maximize)
    {
        System.Type gvType = System.Type.GetType("UnityEditor.GameView,UnityEditor");
        if (gvType == null) return;

        var gv = EditorWindow.GetWindow(gvType, false, "Game", false);
        if (gv == null) return;

        if (maximize && !gv.maximized)
        {
            gv.maximized = true;
        }

        // 关闭 Low Resolution Aspect Ratios 并强制 1.0x 原生像素比例
        var lowResProp = gvType.GetProperty("lowResolutionForAspectRatios", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var scaleField = gvType.GetField("m_defaultScale", BindingFlags.Instance | BindingFlags.NonPublic);
        if (scaleField != null)
        {
            scaleField.SetValue(gv, 1.0f);
        }
        var snapMethod = gvType.GetMethod("SnapZoom", BindingFlags.Instance | BindingFlags.NonPublic);
        if (snapMethod != null)
        {
            snapMethod.Invoke(gv, new object[] { 1.0f });
        }
        gv.Repaint();
    }

    static void OnPlayModeStateChanged(PlayModeStateChange state)
    {
        if (Application.isBatchMode) return;
        if (state == PlayModeStateChange.EnteredPlayMode)
        {
            ApplyUltraQuality();
            MaximizeAndCrispGameView(true);
        }
    }

    static void OnSceneOpened(UnityEngine.SceneManagement.Scene scene, OpenSceneMode mode)
    {
        SessionState.SetBool(SessionKey, false);
        _attempts = 0;
        EditorApplication.update -= Tick;
        EditorApplication.update += Tick;
    }

    static bool HasCommandLineArg(string argName)
    {
        var args = System.Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length; i++)
        {
            if (string.Equals(args[i], argName, System.StringComparison.OrdinalIgnoreCase))
                return true;
        }
        return false;
    }

    static void Tick()
    {
        if (Application.isBatchMode)
        {
            EditorApplication.update -= Tick;
            return;
        }
        if (SessionState.GetBool(SessionKey, false))
        {
            EditorApplication.update -= Tick;
            return;
        }
        if (EditorApplication.isPlayingOrWillChangePlaymode) return;
        if (EditorApplication.isCompiling || EditorApplication.isUpdating) return;

        if (++_attempts > 3600)
        {
            EditorApplication.update -= Tick;
            return;
        }

        var mgr = Object.FindObjectOfType<PortalManager>();
        if (mgr == null) return;

        ApplyUltraQuality();
        mgr.EnsureBuilt();
        mgr.UpdatePortalState();

        var sv = SceneView.lastActiveSceneView;
        if (sv != null && sv.camera != null)
        {
            var target = mgr.transform.position + Vector3.up * (PortalConfig.DoorHeight / 2f);
            sv.LookAt(target, Quaternion.Euler(5f, 0f, 0f), 4.2f);
            if (sv.sceneViewState != null)
            {
                sv.sceneViewState.alwaysRefresh = true;
            }
            sv.Repaint();
        }

        SessionState.SetBool(SessionKey, true);
        Debug.Log("[AutoFramePortal] 已启用 Ultra 8xMSAA 高清画质、移除方格地面并完成三维草海构建。");

        if (HasCommandLineArg("-autoEnterPlayMode") && !SessionState.GetBool(AutoPlayKey, false))
        {
            SessionState.SetBool(AutoPlayKey, true);
            EditorSettings.enterPlayModeOptionsEnabled = false;
            EditorApplication.update -= Tick;
            EditorApplication.EnterPlaymode();
            return;
        }

        EditorApplication.update -= Tick;
    }
}
