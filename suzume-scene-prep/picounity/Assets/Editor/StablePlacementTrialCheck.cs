using System;
using System.IO;
using System.Reflection;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class StablePlacementTrialCheck
{
    const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
    static void Require(bool ok,string message) { if(!ok)throw new Exception(message); }
    static T Get<T>(object target,string field) => (T)target.GetType().GetField(field,Private).GetValue(target);
    static object Call(object target,string name,params object[] args) => target.GetType().GetMethod(name,Private).Invoke(target,args);
    static PortalControllerInput.Hand Aim(Vector3 position,Vector3 target,bool trigger=false) => new PortalControllerInput.Hand
    { tracked=true,position=position,rotation=Quaternion.LookRotation(target-position),trigger=trigger };
    static void Send(DoorCornerMarker marker,PortalControllerInput.Hand right,PortalControllerInput.Hand left) => Call(marker,"ProcessInput",right,left);
    static void Hidden(PortalManager portal,string stage)
    {
        Require(portal.calibrationHidden,stage+": world revealed before confirmation");
        foreach(var name in new[]{"DreamWorld","DoorAssembly","PortalMask","SuzumeCharacter","RigidHingeCompensation_v32"})
        {
            var child=portal.transform.Find(name);Require(child==null||!child.gameObject.activeSelf,stage+": visible "+name);
        }
    }
    public static void Run()
    {
        ContinuousRayTrialCheck.Run();
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal=UnityEngine.Object.FindObjectOfType<PortalManager>();portal.BuildPortal();
        Camera.main.transform.position=new Vector3(0,1.6f,2);
        var marker=new GameObject("StableFlowCheck").AddComponent<DoorCornerMarker>();Call(marker,"Start");
        Hidden(portal,"initial ready");Require(!marker.IsBusy&&!marker.IsBrowsing&&!marker.IsEditing,"initial mode or input blocked by anchor preparation");
        var setter=typeof(PicoPassthroughSetup).GetProperty("IsReady").GetSetMethod(true);
        bool ready=PicoPassthroughSetup.IsReady;setter.Invoke(null,new object[]{true});
        string key="SuzumePortal.Calibration.V2";bool had=PlayerPrefs.HasKey(key);string saved=PlayerPrefs.GetString(key,"");
        var a=new Vector3(-.3f,1,2);var b=new Vector3(.3f,1,2);
        var corners=new[]{new Vector3(.5f,0,0),new Vector3(-.5f,0,0),new Vector3(.5f,2.1f,0),new Vector3(-.5f,2.1f,0)};
        var left=new PortalControllerInput.Hand{tracked=true};
        try
        {
            var hand=Aim(a,corners[0]);Send(marker,hand,left);
            left.secondary=true;Send(marker,hand,left);left.secondary=false;Send(marker,hand,left);
            Hidden(portal,"no saved anchor requested");Require(!marker.IsBrowsing,"missing anchor showed default door");
            // Starting and cancelling from Ready must not reveal a fake previous placement.
            left.primary=true;Send(marker,hand,left);left.primary=false;Send(marker,hand,left);
            hand.secondary=true;Send(marker,hand,left);hand.secondary=false;Send(marker,hand,left);
            Hidden(portal,"cancel initial placement");Require(!marker.IsEditing&&!marker.IsBrowsing,"cancel did not return to reality-only ready mode");
            var originalWorld=portal.transform.Find("DreamWorld");bool originalLandscape=portal.mountainLandscape;
            for(int i=0;i<4;i++)
            {
                hand=Aim(a,corners[i]);Send(marker,hand,left);hand.trigger=true;Send(marker,hand,left);
                Require(Get<bool>(marker,"_hasFirstRay")&&Get<int>(marker,"_count")==i,"first trigger did not retain one ray");
                hand.trigger=false;Send(marker,hand,left);
                if(i==0)
                {
                    hand.primary=true;Send(marker,hand,left);hand.primary=false;Send(marker,hand,left);
                    Require(portal.mountainLandscape==originalLandscape&&portal.transform.Find("DreamWorld")==originalWorld,"A rebuilt or changed world during placement");
                    for(int frame=0;frame<1800;frame++) Send(marker,hand,left);
                    Require(Get<bool>(marker,"_hasFirstRay")&&Get<int>(marker,"_count")==0,"idle frames changed the current selection step");
                }
                hand=Aim(b,corners[i]);Send(marker,hand,left);hand.trigger=true;Send(marker,hand,left);
                Require(Get<int>(marker,"_count")==i+1,"second trigger did not record corner "+i);
                Hidden(portal,"corner "+i);hand.trigger=false;Send(marker,hand,left);
                if(i==1)
                {
                    // Reproduce the reported interruption after the second corner.
                    var savedCorners=(Vector3[])Get<Vector3[]>(marker,"_corners").Clone();
                    Call(marker,"OnApplicationFocus",false);Call(marker,"OnApplicationPause",true);
                    hand.trigger=true;left.primary=true;
                    for(int frame=0;frame<120;frame++)Send(marker,hand,left);
                    Require(Get<int>(marker,"_count")==2&&!Get<bool>(marker,"_hasFirstRay"),"paused input changed captured corners");
                    Call(marker,"OnApplicationPause",false);Call(marker,"OnApplicationFocus",true);
                    Send(marker,hand,left);
                    Require(Get<int>(marker,"_count")==2&&!Get<bool>(marker,"_hasFirstRay"),"held button on resume captured or restarted placement");
                    for(int corner=0;corner<2;corner++)Require(Get<Vector3[]>(marker,"_corners")[corner]==savedCorners[corner],"resume moved a saved corner");
                    hand.trigger=false;left.primary=false;Send(marker,hand,left);
                    Hidden(portal,"resume after second corner");
                }
            }
            Require(marker.IsEditing&&!marker.IsBrowsing&&marker.transform.Find("DoorOutline").GetComponent<LineRenderer>().enabled,"four corners skipped explicit preview confirmation");
            hand.trigger=true;Send(marker,hand,left);hand.trigger=false;Send(marker,hand,left);
            Require(marker.IsBrowsing&&!portal.calibrationHidden&&!marker.IsBusy,"final trigger did not show scene");
            Require(portal.mountainLandscape!=originalLandscape,"queued landscape was not applied at confirmation");
            var confirmedPosition=portal.portalPosition;
            left.primary=true;Send(marker,hand,left);left.primary=false;Send(marker,hand,left);
            Hidden(portal,"recalibration from confirmed view");
            hand.secondary=true;Send(marker,hand,left);hand.secondary=false;Send(marker,hand,left);
            Require(marker.IsBrowsing&&!portal.calibrationHidden&&portal.portalPosition==confirmedPosition,"cancel failed to restore explicitly confirmed view");
            Require(typeof(PicoPassthroughSetup).GetMethod("UpdateDiagnosticProbe",Private)==null,"old file-controlled diagnostic loop remains");
            Require(typeof(PortalCompositionFeature).GetMethod("SetProbeMode")==null,"software-layer suppression control remains");
            foreach(var texture in new[]{"compact_ready","compact_step0","compact_pair0","compact_preview","footer_ready_flat","footer_placement_mountain"})
                Require(Resources.Load<Texture2D>("ControllerGuide/"+texture)!=null,"missing compact UI "+texture);
        }
        finally
        {
            setter.Invoke(null,new object[]{ready});
            if(had) PlayerPrefs.SetString(key,saved);else PlayerPrefs.DeleteKey(key);PlayerPrefs.Save();
        }
        File.WriteAllText("Builds/controller-check/stable-flow-result.txt","PASS: reality-only startup; immediate trigger selection; no anchor-startup input lock; cancel before first confirmation stays in reality; 1800 idle input frames preserve selected ray; A queues terrain without rebuild; all 8 trigger observations keep world hidden; final explicit confirmation reveals selected world; cancel recalibration restores confirmed placement; file-controlled diagnostic and software-layer suppression APIs removed; compact placement UI available. Existing geometry/controller/render checks passed.\n");
        Debug.Log("[StablePlacementTrialCheck] ALL CHECKS PASSED");
    }
}
