using UnityEngine;
using UnityEditor;
using System.IO;
using System.Text;

/// <summary>
/// Play 模式运行时测试：真正进入 Play 模式，验证 PortalManager.Start() + PortalCalibrationUI 运行时构建与渲染。
/// </summary>
public static class PlayModeTest
{
    const string OutPng = "D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity/preview/unity-playmode-运行时.png";
    const string OutDiag = "D:/Unity/portal-playmode-diag.txt";

    static StringBuilder _sb;
    static int _frames;
    static bool _armed;
    static int _guard;

    public static void Run()
    {
        _sb = new StringBuilder();
        Application.SetStackTraceLogType(LogType.Log, StackTraceLogType.None);

        EditorSettings.enterPlayModeOptionsEnabled = true;
        EditorSettings.enterPlayModeOptions = EnterPlayModeOptions.DisableDomainReload;

        SceneBootstrap.BuildScene();
        _sb.AppendLine("场景重建: OK");
        _sb.AppendLine("进入 Play 模式前，场景内 PortalManager 数: " + Object.FindObjectsOfType<PortalManager>().Length);

        EditorApplication.update += Tick;
        _armed = true;
        EditorApplication.EnterPlaymode();
    }

    static void Tick()
    {
        _guard++;
        if (_guard > 20000)
        {
            _sb.AppendLine("超时退出");
            Finish(1);
            return;
        }
        if (!EditorApplication.isPlaying) return;

        _frames++;
        if (_frames < 30) return;

        _sb.AppendLine($"Play 中帧数: {_frames}");

        var mgr = Object.FindObjectOfType<PortalManager>();
        var ui = Object.FindObjectOfType<PortalCalibrationUI>();
        var mask = GameObject.Find("PortalMask");
        var dream = GameObject.Find("DreamWorld");
        var chara = GameObject.Find("SuzumeCharacter");
        var doorAssem = GameObject.Find("DoorAssembly");
        var root = GameObject.Find("SuzumePortalRoot");

        _sb.AppendLine($"运行时对象存在: root={root != null} mask={mask != null} dreamWorld={dream != null} "
                       + $"character={chara != null} doorAssembly={doorAssem != null} ui={ui != null}");

        foreach (var s in new[] { "Suzume/PortalMask", "Suzume/PortalTarget", "Suzume/DoorFrame", "Suzume/DoorOcclusion" })
            _sb.AppendLine($"  Shader.Find(\"{s}\") = " + (Shader.Find(s) != null ? "OK" : "NOT FOUND"));

        var cam = Camera.main;
        if (cam != null)
        {
            int W = 1440, H = 900;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32);
            rt.antiAliasing = 4;
            rt.Create();
            var saved = cam.targetTexture;
            cam.targetTexture = rt;
            cam.Render();

            RenderTexture.active = rt;
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, W, H), 0, 0);
            tex.Apply();
            RenderTexture.active = null;
            cam.targetTexture = saved;

            var png = tex.EncodeToPNG();
            File.WriteAllBytes(OutPng, png);
            _sb.AppendLine($"Play 模式渲染输出: {OutPng} ({png.Length} bytes)");

            rt.Release();
            Object.DestroyImmediate(rt);
            Object.DestroyImmediate(tex);
        }

        Finish(0);
    }

    static void Finish(int code)
    {
        if (!_armed) { EditorApplication.Exit(code); return; }
        _armed = false;
        if (EditorApplication.isPlaying) EditorApplication.ExitPlaymode();
        File.WriteAllText(OutDiag, _sb.ToString(), Encoding.UTF8);
        Debug.Log("[PlayModeTest]\n" + _sb);
        EditorApplication.Exit(code);
    }
}
