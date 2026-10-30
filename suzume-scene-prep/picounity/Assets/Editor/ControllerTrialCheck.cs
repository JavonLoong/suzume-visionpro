using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using PicoController = UnityEngine.XR.OpenXR.Features.Interactions.PICO4UltraControllerProfile.PICO4UltraController;

public static class ControllerTrialCheck
{
    static void Require(bool value, string message) { if (!value) throw new Exception(message); }
    public static void Run()
    {
        CheckControllerInput();
        var p = new[] { new Vector3(.5f,0,0), new Vector3(-.5f,0,0), new Vector3(.5f,2.1f,0), new Vector3(-.5f,2.1f,0) };
        Require(DoorCalibrationMath.TryFit(p,new Vector3(0,1.6f,2),out var fit,out _),"basic four-point fit failed");
        Require(Mathf.Abs(fit.width-1)<.001f && Mathf.Abs(fit.height-2.1f)<.001f,"measured size incorrect");
        Require(Vector3.Dot(fit.rotation*Vector3.forward,Vector3.forward)>.999f,"door faces away from observer");
        var rotation=Quaternion.Euler(0,63,0); var center=new Vector3(4,.3f,-3);
        var rotated=new Vector3[4]; for(int i=0;i<4;i++) rotated[i]=center+rotation*p[i];
        Require(DoorCalibrationMath.TryFit(rotated,center+rotation*new Vector3(0,1.6f,2),out var fit2,out _),"rotated/translated fit failed");
        Require(Vector3.Distance(fit2.center,center)<.001f && Quaternion.Angle(fit2.rotation,rotation)<.01f,"rotated pose incorrect");
        var swapped=new[]{p[1],p[0],p[3],p[2]};
        Require(!DoorCalibrationMath.TryFit(swapped,new Vector3(0,1.6f,2),out _,out _),"reversed corner order accepted");
        var crossed=new[]{p[0],p[1],p[3],p[2]};
        Require(!DoorCalibrationMath.TryFit(crossed,new Vector3(0,1.6f,2),out _,out _),"crossed upper corners accepted");
        var bad=new[]{p[0],p[0],p[2],p[3]};
        Require(!DoorCalibrationMath.TryFit(bad,new Vector3(0,1.6f,2),out _,out _),"zero width accepted");
        // Render both variants using the actual scene and imported assets.
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal=UnityEngine.Object.FindObjectOfType<PortalManager>(); Require(portal!=null,"portal missing");
        portal.portalPosition=Vector3.zero;portal.portalYaw=0;portal.portalHeight=2.1f;portal.portalWidth=1f;
        portal.mountainLandscape=false;portal.BuildPortal();
        Require(Mathf.Abs(portal.transform.lossyScale.x*PortalConfig.BaseDoorWidth-1f)<.001f,"measured width not applied to opening");
        Directory.CreateDirectory("Builds/controller-check");
        var cam=Camera.main;cam.transform.SetPositionAndRotation(new Vector3(0,1.6f,2.7f),Quaternion.Euler(0,180,0));
        cam.fieldOfView=60;cam.farClipPlane=800;
        SaveImage(cam,"flat");
        float flatHeight=TerrainTop(portal);
        portal.SetLandscape(true);SaveImage(cam,"mountain");
        float mountainHeight=TerrainTop(portal);
        Require(mountainHeight>flatHeight+2f,"mountain variant does not restore higher source terrain");
        portal.SetLandscape(false);Require(portal.portalWidth==1f && portal.portalPosition==Vector3.zero,"scene switch changed placement");
        portal.calibrationHidden=true;portal.UpdatePortalState();
        Require(!portal.transform.Find("DreamWorld").gameObject.activeSelf,"landscape obscures physical corners during calibration");
        portal.calibrationHidden=false;portal.UpdatePortalState();
        foreach(var name in new[]{"intro","step0","step1","step2","step3","pair0","pair1","pair2","pair3","ray_baseline","ray_parallel","ray_range","gap_label","gap_digits","preview","saved","session","wait","busy","footer_flat","footer_mountain"})
            Require(Resources.Load<Texture2D>("ControllerGuide/"+name)!=null,"missing guide: "+name);
        var guide=new GameObject("GuidePreview").AddComponent<PortalGuideView>();guide.Initialize(cam);
        guide.Show("intro",true,false);SaveImage(cam,"guide-intro");
        portal.calibrationHidden=true;portal.UpdatePortalState();PicoPassthroughSetup.ConfigureCamera(cam);
        guide.Show("ready",true,false,PortalGuideView.Context.Ready);SaveImage(cam,"guide-ready");
        guide.Show("step0",true,false,PortalGuideView.Context.Placement);SaveImage(cam,"guide-step1");
        guide.Show("pair0",true,false,PortalGuideView.Context.Placement);guide.ShowRayGap(.123f,true);SaveImage(cam,"guide-second-ray");
        guide.ShowRayGap(.023f,true);SaveImage(cam,"guide-near-rays");guide.ShowRayGap(0,false);
        guide.Show("preview",true,false,PortalGuideView.Context.Placement);SaveImage(cam,"guide-confirm");
        portal.calibrationHidden=false;portal.UpdatePortalState();
        guide.Show("intro",false,false);SaveImage(cam,"guide-collapsed");
        UnityEngine.Object.DestroyImmediate(guide.gameObject);
        File.WriteAllText("Builds/controller-check/result.txt",$"PASS: actual PICO controller layout button/pose reads, tracking loss, geometry, reversed/crossed/duplicate point rejection, measured width, both scenes, placement retained, calibration visibility, guide textures and rendered UI. Flat terrain max={flatHeight:F2}m; restored mountain max={mountainHeight:F2}m.\n");
        Debug.Log("[ControllerTrialCheck] ALL CHECKS PASSED");
    }
    static void CheckControllerInput()
    {
        InputSystem.RegisterLayout<UnityEngine.XR.OpenXR.Input.HapticControl>("Haptic");
        InputSystem.RegisterLayout(typeof(PicoController).GetProperty("devicePose").PropertyType,"Pose");
        InputSystem.RegisterLayout<PicoController>("PortalCheckPico");
        var right=(PicoController)InputSystem.AddDevice("PortalCheckPico");
        var left=(PicoController)InputSystem.AddDevice("PortalCheckPico");
        try
        {
            InputSystem.SetDeviceUsage(right,UnityEngine.InputSystem.CommonUsages.RightHand);
            InputSystem.SetDeviceUsage(left,UnityEngine.InputSystem.CommonUsages.LeftHand);
            foreach(var device in new[]{right,left})
            {
                using(StateEvent.From(device,out var evt))
                {
                    device.isTracked.WriteValueIntoEvent(1f,evt);device.trackingState.WriteValueIntoEvent(3,evt);
                    device.pointerPosition.WriteValueIntoEvent(new Vector3(.2f,1.4f,-.3f),evt);
                    device.pointerRotation.WriteValueIntoEvent(Quaternion.Euler(0,40,0),evt);
                    device.primaryButton.WriteValueIntoEvent(1f,evt);device.secondaryButton.WriteValueIntoEvent(1f,evt);
                    device.triggerPressed.WriteValueIntoEvent(1f,evt);device.gripPressed.WriteValueIntoEvent(1f,evt);
                    InputState.Change(device,evt);
                }
            }
            foreach(bool isRight in new[]{true,false})
            {
                var hand=PortalControllerInput.Read(isRight);
                Require(hand.tracked&&hand.primary&&hand.secondary&&hand.trigger&&hand.grip,"PICO face/trigger/grip mapping failed");
                Require(Vector3.Distance(hand.position,new Vector3(.2f,1.4f,-.3f))<.001f,"PICO pointer pose read failed");
            }
            using(StateEvent.From(right,out var evt)) { right.isTracked.WriteValueIntoEvent(0f,evt);InputState.Change(right,evt); }
            Require(!PortalControllerInput.Read(true).tracked,"lost controller tracking accepted");
            InputState.Change(left.trackingState,1);
            Require(!PortalControllerInput.Read(false).tracked,"partial controller pose accepted");
        }
        finally{InputSystem.RemoveDevice(right);InputSystem.RemoveDevice(left);InputSystem.RemoveLayout("PortalCheckPico");}
    }
    static float TerrainTop(PortalManager portal)
    {
        foreach(var m in portal.transform.Find("DreamWorld").GetComponentsInChildren<MeshFilter>())
            if(m.name.Contains("NearMeadow")||m.name.Contains("Geometry_C7FAF2CB"))
            {var bounds=m.GetComponent<Renderer>().bounds;return bounds.max.y;}
        throw new Exception("terrain mesh missing");
    }
    static void SaveImage(Camera cam,string name)
    {
        var rt=new RenderTexture(1200,900,24);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;
        var tex=new Texture2D(1200,900,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,1200,900),0,0);tex.Apply();
        File.WriteAllBytes("Builds/controller-check/"+name+".png",tex.EncodeToPNG());
        cam.targetTexture=null;RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(tex);UnityEngine.Object.DestroyImmediate(rt);
    }
}
