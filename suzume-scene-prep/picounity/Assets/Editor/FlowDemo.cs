using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// 按玩家顺序拍下双世界：门外关门、推开、看见铃芽、侧面、跨进异世界、回头。
/// </summary>
public static class FlowDemo
{
    const string Dir = "D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity/preview/flow";

    public static void Run()
    {
        Directory.CreateDirectory(Dir);
        SceneBootstrap.BuildScene();
        var mgr = Object.FindObjectOfType<PortalManager>();
        if (mgr == null)
        {
            Debug.LogError("FlowDemo: 没有 PortalManager");
            EditorApplication.Exit(1);
            return;
        }
        mgr.EnsureBuilt();
        var cam = Camera.main;
        if (cam == null)
        {
            var go = new GameObject("FlowCam");
            cam = go.AddComponent<Camera>();
            go.tag = "MainCamera";
        }
        cam.fieldOfView = PortalConfig.DefaultCameraFov;
        cam.nearClipPlane = 0.05f;
        cam.farClipPlane = 1200f;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.09f, 0.12f, 0.11f, 1f);

        mgr.fullMeadowView = false;
        mgr.frameMode = PortalConfig.FrameMode.Reference;
        mgr.showDoorLeaf = true;
        mgr.showCharacter = true;
        mgr.showOutsideReferenceFloor = true;
        mgr.characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;

        Shot(mgr, cam, "01-门外关门", 0f, new Vector3(0f, 1.58f, 2.8f), new Vector3(0f, 1.15f, 0f), false);
        Shot(mgr, cam, "02-把门推开", 42f, new Vector3(0.15f, 1.55f, 2.4f), new Vector3(0f, 1.2f, -0.4f), false);
        Shot(mgr, cam, "03-洞里看见铃芽", PortalConfig.MovieDoorOpenAngle, new Vector3(0f, 1.6f, 2.6f), new Vector3(0f, 1.15f, -1.2f), false);
        Shot(mgr, cam, "04-侧面两个世界", PortalConfig.MovieDoorOpenAngle, new Vector3(-1.15f, 1.55f, 2.15f), new Vector3(0.05f, 1.15f, -0.2f), false);
        Shot(mgr, cam, "05-跨进异世界", PortalConfig.MovieDoorOpenAngle, new Vector3(0.1f, 1.62f, -1.6f), new Vector3(0f, 1.1f, -8f), false);
        Shot(mgr, cam, "06-回头看门", PortalConfig.MovieDoorOpenAngle, new Vector3(-0.4f, 1.6f, -2.4f), new Vector3(0f, 1.3f, 0.2f), false);

        EditorSceneManager.SaveOpenScenes();
        Debug.Log("FlowDemo 六张已写入 " + Dir);
    }

    static void Shot(PortalManager mgr, Camera cam, string name, float angle, Vector3 pos, Vector3 look, bool full)
    {
        mgr.doorOpenAngle = angle;
        mgr.fullMeadowView = full;
        cam.transform.position = pos;
        cam.transform.LookAt(look);
        mgr.UpdatePortalState();
        var rt = new RenderTexture(1280, 800, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        rt.Create();
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        var tex = new Texture2D(1280, 800, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, 1280, 800), 0, 0);
        tex.Apply();
        RenderTexture.active = null;
        cam.targetTexture = null;
        File.WriteAllBytes(Dir + "/" + name + ".png", tex.EncodeToPNG());
        Object.DestroyImmediate(tex);
        rt.Release();
        Object.DestroyImmediate(rt);
    }
}
