using System;
using System.IO;
using System.Reflection;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class DoorAdjustmentTrialCheck
{
    const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
    static object Call(object target,string name,params object[] args)=>target.GetType().GetMethod(name,Private).Invoke(target,args);
    static T Get<T>(object target,string name)=>(T)target.GetType().GetField(name,Private).GetValue(target);
    static void Require(bool ok,string why){if(!ok)throw new Exception(why);}
    static void Equal(Vector3[] a,Vector3[] b,string why){Require(a.Length==b.Length,why);for(int i=0;i<a.Length;i++)Require(Vector3.Distance(a[i],b[i])<1e-5f,why+" corner="+i);}
    sealed class Detector:IDoorKeypointDetector,IDoorGuidedDetector
    {
        public void Reset(){}
        public bool TryDetect(DoorCameraFrame f,Vector2[] p,float[] c)=>false;
        public bool TryDetectGuided(DoorCameraFrame f,Rect r,Vector2[] p,float[] c)=>false;
    }
    public static void Run()
    {
        EnterpriseCameraTrialCheck.Run();AsyncDoorTrialCheck.Run();MathChecks();FlowChecks();
        File.WriteAllText("D:/suzume-door-tuning-20261120/adjustment-check.txt","PASS: controller stick mapping, user candidate freeze, four independent 3-D corners, whole-quad translation, actual mask mesh corners, pause guard, cancel restore, explicit confirmation, local calibration round trip, anchor-local JSON round trip, tilted pose and capture-time relative pose conversion. Hardware anchor persistence still requires headset test.\n");
        Debug.Log("[DoorAdjustmentTrialCheck] ALL CHECKS PASSED");
    }
    static void MathChecks()
    {
        var points=DoorQuadPlacement.Rectangle(new Vector3(.2f,.3f,.4f),Quaternion.Euler(12,35,7),.024f,.056f);
        points[3]+=new Vector3(.001f,.002f,.003f);
        Require(DoorQuadPlacement.TryFit(points,out var fit),"valid non-planar small door rejected");
        var local=DoorQuadPlacement.ToLocal(points,fit.center,fit.rotation);
        Equal(DoorQuadPlacement.ToWorld(local,fit.center,fit.rotation),points,"anchor round-trip");
        var root=Matrix4x4.TRS(new Vector3(3,1,5),Quaternion.Euler(0,75,0),Vector3.one);
        var current=new Pose(new Vector3(.03f,1.2f,.04f),Quaternion.Euler(2,12,3));
        var captured=new Pose(new Vector3(.02f,1.2f,.02f),Quaternion.Euler(1,8,2));
        var now=root*EnterpriseDoorCamera.NativeHeadToUnity(current);
        Require(EnterpriseDoorCamera.TryCapturePose(now,captured,current,out var atCapture),"valid capture motion rejected");
        var expected=root*EnterpriseDoorCamera.NativeHeadToUnity(captured);
        for(int i=0;i<16;i++)Require(Mathf.Abs(atCapture[i]-expected[i])<1e-5f,"capture pose mixed tracking/world origin");
        var invalidPose=captured;invalidPose.rotation.x=float.NaN;
        Require(!EnterpriseDoorCamera.TryCapturePose(now,invalidPose,current,out _),"NaN capture rotation accepted");
        var corrupt=(Vector3[])points.Clone();corrupt[0].x=float.NaN;
        Require(!DoorQuadPlacement.TryFit(corrupt,out _),"NaN quad accepted");
        corrupt=(Vector3[])points.Clone();corrupt[3]=corrupt[0];Require(!DoorQuadPlacement.TryFit(corrupt,out _),"collapsed quad accepted");
        var state=new DoorPoseStabilizer{assumeUpright=false};
        Get<System.Collections.Generic.List<DoorPoseSolver.Observation>>(state,"_window").Add(default);
        var copy=state.Snapshot();state.Reset();Require(copy.ObservationCount==1&&state.ObservationCount==0,"worker shares mutable observations");
        state.CopyFrom(copy);Require(state.ObservationCount==1&&!state.assumeUpright,"stabilizer publish lost data");
    }
    static void FlowChecks()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");var portal=UnityEngine.Object.FindObjectOfType<PortalManager>();portal.BuildPortal();
        var cam=Camera.main;cam.transform.SetPositionAndRotation(new Vector3(0,.035f,.14f),Quaternion.Euler(0,180,0));
        var marker=new GameObject("CornerAdjustmentCheck").AddComponent<DoorCornerMarker>();Call(marker,"Start");
        var detector=DoorAutoLocator.Detector;DoorAutoLocator.Detector=new Detector();
        var locator=new GameObject("CornerAdjustmentLocator").AddComponent<DoorAutoLocator>();Call(locator,"Awake");
        var property=typeof(PicoPassthroughSetup).GetProperty("IsReady");var setter=property.GetSetMethod(true);bool oldReady=PicoPassthroughSetup.IsReady;setter.Invoke(null,new object[]{true});
        string key="SuzumePortal.Calibration.V2";bool had=PlayerPrefs.HasKey(key);string saved=PlayerPrefs.GetString(key,"");
        var r=new PortalControllerInput.Hand{tracked=true,position=new Vector3(.01f,.02f,.1f),rotation=Quaternion.Euler(0,180,0)};
        var l=new PortalControllerInput.Hand{tracked=true};void Send()=>Call(marker,"ProcessInput",r,l);
        try
        {
            Send();r.trigger=true;Send();r.trigger=false;Send();Require(marker.IsGuiding,"guide did not start");
            var pose=new DoorPoseSolver.Solution{position=Vector3.zero,rotation=Quaternion.Euler(7,0,4)};
            Require(marker.ShowDetectedDoor(pose,.024f,.056f),"candidate not shown");r.trigger=true;Send();
            Require(marker.IsEditing&&!marker.IsGuiding&&!marker.IsBrowsing&&!locator.hint.Active,"explicit freeze failed");
            var frozen=(Vector3[])Get<Vector3[]>(marker,"_corners").Clone();
            Require(!marker.ShowDetectedDoor(new DoorPoseSolver.Solution{position=Vector3.one,rotation=Quaternion.identity},.024f,.056f),"recognition moved frozen target");
            r.trigger=false;Send();r.stickClick=true;Send();r.stickClick=false;Send();
            Require(marker.IsTuning,"stick click did not enter adjustment");
            l.stick=Vector2.right;r.stick=Vector2.up;Send();
            var moved=Get<Vector3[]>(marker,"_corners");
            for(int i=0;i<4;i++)Require(Vector3.Distance(moved[i],frozen[i]+(Get<Vector3>(marker,"_adjustRight")+Vector3.up)*.0005f)<1e-6f,"joystick direction/step mismatch");
            l.stick=Vector2.zero;r.stick=Vector2.zero;Send();r.primary=true;Send();r.primary=false;Send();Require(marker.AdjustmentTarget==1,"A did not select bottom left");
            l.secondary=true;Send();l.secondary=false;Send();Require(!Get<bool>(marker,"_fine"),"Y did not switch step size");
            r.secondary=true;Send();r.secondary=false;Send();Equal(Get<Vector3[]>(marker,"_corners"),frozen,"cancel joystick edits changed original");
            r.stickClick=true;Send();r.stickClick=false;Send();
            for(int target=1;target<=4;target++)foreach(var axis in new[]{Vector3.right,Vector3.left,Vector3.up,Vector3.down,Vector3.forward,Vector3.back})
            {
                var before=(Vector3[])Get<Vector3[]>(marker,"_corners").Clone();
                Require(marker.TryAdjust(target,axis*.0005f),"valid six-direction nudge rejected");
                var after=Get<Vector3[]>(marker,"_corners");for(int i=0;i<4;i++)Require(Vector3.Distance(after[i],before[i]+(i==target-1?axis*.0005f:Vector3.zero))<1e-6f,"wrong corner moved");
            }
            Require(marker.TryAdjust(0,new Vector3(.001f,.002f,.003f)),"whole quad nudge rejected");
            var whole=Get<Vector3[]>(marker,"_corners");for(int i=0;i<4;i++)Require(Vector3.Distance(whole[i],frozen[i]+new Vector3(.001f,.002f,.003f))<1e-5f,"whole shift distorted shape");
            Call(marker,"OnApplicationFocus",false);Require(!marker.TryAdjust(0,Vector3.right*.001f),"unfocused edit accepted");Call(marker,"OnApplicationFocus",true);
            Send();r.secondary=true;Send();r.secondary=false;Send();Equal(Get<Vector3[]>(marker,"_corners"),frozen,"cancel did not restore exact quad");
            r.stickClick=true;Send();r.stickClick=false;Send();Require(marker.IsTuning,"reenter tune failed");
            Require(marker.TryAdjust(4,new Vector3(.001f,.001f,.002f)),"independent top corner failed");
            var adjusted=(Vector3[])Get<Vector3[]>(marker,"_corners").Clone();
            AssertMask(portal,adjusted);
            // JSON persistence stores coordinates relative to the anchor, not process/world coordinates.
            var fit=Get<DoorCalibrationMath.Placement>(marker,"_fit");var savedType=typeof(DoorCornerMarker).GetNestedType("SavedPlacement",BindingFlags.NonPublic);
            var record=Activator.CreateInstance(savedType);savedType.GetField("corners").SetValue(record,DoorQuadPlacement.ToLocal(adjusted,fit.center,fit.rotation));
            string json=JsonUtility.ToJson(record);var restored=JsonUtility.FromJson(json,savedType);
            Equal(DoorQuadPlacement.ToWorld((Vector3[])savedType.GetField("corners").GetValue(restored),fit.center,fit.rotation),adjusted,"anchor JSON lost corner edits");
            r.trigger=false;Send();r.trigger=true;Send();r.trigger=false;Send();Require(marker.IsBrowsing&&!portal.calibrationHidden,"save did not show scene");
            Equal(portal.GetWorldCorners(),adjusted,"confirmation changed quad");
            portal.SaveCalibration();portal.SetWorldCorners(null);portal.useFullRotation=false;portal.RestoreCalibration();
            Equal(portal.GetWorldCorners(),adjusted,"calibration restore lost tilt/corners");AssertMask(portal,adjusted);
            r.stickClick=true;Send();r.stickClick=false;Send();marker.TryAdjust(2,new Vector3(-.001f,0,.001f));
            r.primary=true;Send();r.primary=false;Send();r.primary=true;Send();r.primary=false;Send();
            Require(marker.AdjustmentTarget==2,"rendered target selection mismatch");
            var guide=Get<PortalGuideView>(marker,"_guide");guide.Show("tune_2_fine",true,false,PortalGuideView.Context.Placement);
            var rt=new RenderTexture(1200,900,24);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;
            var image=new Texture2D(1200,900,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,1200,900),0,0);image.Apply();
            File.WriteAllBytes("D:/suzume-door-tuning-20261120/adjustment-ui.png",image.EncodeToPNG());cam.targetTexture=null;RenderTexture.active=null;
            UnityEngine.Object.DestroyImmediate(image);UnityEngine.Object.DestroyImmediate(rt);
            r.secondary=true;Send();Require(marker.IsBrowsing,"browse adjustment cancel did not return to display");Equal(portal.GetWorldCorners(),adjusted,"browse cancel lost saved corners");
        }
        finally
        {
            setter.Invoke(null,new object[]{oldReady});DoorAutoLocator.Detector=detector;
            UnityEngine.Object.DestroyImmediate(locator.gameObject);UnityEngine.Object.DestroyImmediate(marker.gameObject);
            if(had)PlayerPrefs.SetString(key,saved);else PlayerPrefs.DeleteKey(key);PlayerPrefs.Save();
        }
    }
    static void AssertMask(PortalManager portal,Vector3[] expected)
    {
        var mask=portal.transform.Find("PortalMask");var vertices=mask.GetComponent<MeshFilter>().sharedMesh.vertices;
        foreach(var corner in expected){float closest=float.PositiveInfinity;foreach(var vertex in vertices)closest=Mathf.Min(closest,Vector3.Distance(mask.TransformPoint(vertex),corner));Require(closest<1e-5f,"actual aperture mesh does not follow edited corner");}
    }
}
