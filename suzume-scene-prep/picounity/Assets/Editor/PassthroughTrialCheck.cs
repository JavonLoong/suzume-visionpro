using System;
using System.IO;
using System.Reflection;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class PassthroughTrialCheck
{
    static void Require(bool ok, string message) { if (!ok) throw new Exception(message); }
    static object Call(object target, string name, params object[] args) => target.GetType().GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic).Invoke(target, args);
    static void Hidden(PortalManager portal, string stage)
    {
        Require(portal.calibrationHidden, stage + ": hidden flag lost");
        foreach (string name in new[] { "DreamWorld", "PortalMask", "DoorAssembly", "RigidHingeCompensation_v32", "SuzumeCharacter", "OutsideReferenceFloor" })
        {
            var child = portal.transform.Find(name);
            Require(child == null || !child.gameObject.activeInHierarchy, stage + ": " + name + " covers the room");
        }
        Require(Camera.main.clearFlags == CameraClearFlags.SolidColor && Camera.main.backgroundColor.a == 0, stage + ": opaque camera background");
        Require(!Camera.main.allowHDR, stage + ": HDR may discard the camera alpha channel");
    }
    public static void Run()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal = UnityEngine.Object.FindObjectOfType<PortalManager>();
        Require(portal != null && Camera.main != null, "scene components missing");
        portal.BuildPortal();
        Camera.main.transform.position = new Vector3(0, 1.6f, 2);
        portal.fullMeadowView = true;
        portal.frameMode = PortalConfig.FrameMode.Occlusion;
        portal.showDoorLeaf = true;
        var before = portal.portalPosition;
        var marker = new GameObject("PassthroughStateCheck").AddComponent<DoorCornerMarker>();
        Call(marker, "Start");
        var modeField=typeof(DoorCornerMarker).GetField("_mode",BindingFlags.Instance|BindingFlags.NonPublic);
        modeField.SetValue(marker,Enum.Parse(modeField.FieldType,"Browse"));
        portal.calibrationHidden=false;portal.UpdatePortalState();
        Call(marker, "Begin");
        Hidden(portal, "begin from immersive view");
        var cam=Camera.main;var originalTarget=cam.targetTexture;var previousActive=RenderTexture.active;
        var rgbaTarget=new RenderTexture(256,256,24,RenderTextureFormat.ARGB32);
        var rgbaPixels=new Texture2D(256,256,TextureFormat.RGBA32,false);
        try
        {
            cam.targetTexture=rgbaTarget;cam.Render();RenderTexture.active=rgbaTarget;
            rgbaPixels.ReadPixels(new Rect(0,0,256,256),0,0);rgbaPixels.Apply();
            foreach(var uv in new[]{new Vector2(.05f,.05f),new Vector2(.95f,.95f),new Vector2(.05f,.95f)})
                Require(rgbaPixels.GetPixelBilinear(uv.x,uv.y).a<.01f,"calibration background rendered opaque pixels");
        }
        finally { cam.targetTexture=originalTarget;RenderTexture.active=previousActive;UnityEngine.Object.DestroyImmediate(rgbaTarget);UnityEngine.Object.DestroyImmediate(rgbaPixels); }
        var corners = new[] { new Vector3(.5f,0,0), new Vector3(-.5f,0,0), new Vector3(.5f,2.1f,0), new Vector3(-.5f,2.1f,0) };
        foreach (var point in corners) Call(marker, "Add", point);
        Hidden(portal, "four-point preview");
        Require(marker.IsEditing, "preview exited editing before confirmation");
        var outline = marker.transform.Find("DoorOutline").GetComponent<LineRenderer>();
        Require(outline.enabled && outline.positionCount == 5, "physical door outline missing");
        portal.SetLandscape(!portal.mountainLandscape);
        Hidden(portal, "landscape switch during preview");
        Call(marker, "Undo");
        Hidden(portal, "undo");
        Require(!outline.enabled, "stale preview outline after undo");
        Call(marker, "Cancel");
        Require(!marker.IsEditing && !portal.calibrationHidden, "cancel did not restore browsing");
        Require(portal.portalPosition == before && portal.fullMeadowView && portal.showDoorLeaf && portal.frameMode == PortalConfig.FrameMode.Occlusion, "cancel lost previous placement/display");
        Call(marker, "Begin");
        Hidden(portal, "restart");
        foreach (var point in corners) Call(marker, "Add", point);
        Hidden(portal, "second preview");
        // A real device/provider is intentionally absent. Verify the current-session confirmation path.
        string key = "SuzumePortal.Calibration.V2";
        bool had = PlayerPrefs.HasKey(key); string saved = PlayerPrefs.GetString(key, "");
        try
        {
            var task = (System.Threading.Tasks.Task)Call(marker, "Confirm");
            Require(task.IsCompleted, "no-provider confirmation unexpectedly waits");
            task.GetAwaiter().GetResult();
            Require(!marker.IsEditing && !portal.calibrationHidden && !portal.fullMeadowView, "confirmation did not reveal portal");
            Require(portal.transform.Find("DreamWorld").gameObject.activeSelf, "confirmed world is still hidden");
            Require(portal.frameMode == PortalConfig.FrameMode.Occlusion && portal.showDoorLeaf, "confirmation changed original frame/leaf setting");
        }
        finally { if (had) PlayerPrefs.SetString(key, saved); else PlayerPrefs.DeleteKey(key); PlayerPrefs.Save(); }
        Require(Resources.Load<Texture2D>("ControllerGuide/passthrough_wait") != null, "missing real-world wait guide");
        Directory.CreateDirectory("Builds/controller-check");
        File.WriteAllText("Builds/controller-check/passthrough-result.txt", "PASS: transparent camera; virtual environment, mask, character, door and floor hidden through begin/collect/preview/undo/restart/landscape switch; outline visible in preview; cancel restores placement; confirm reveals portal. Hardware camera feed requires headset verification.\n");
        Debug.Log("[PassthroughTrialCheck] ALL CHECKS PASSED");
    }
}
