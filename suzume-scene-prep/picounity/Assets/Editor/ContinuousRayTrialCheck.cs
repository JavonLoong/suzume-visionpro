using System;
using System.IO;
using System.Reflection;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class ContinuousRayTrialCheck
{
    const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
    static void Require(bool value,string reason) { if(!value)throw new Exception(reason); }
    static void Set(object target,string field,object value) => target.GetType().GetField(field,Private).SetValue(target,value);
    static T Get<T>(object target,string field) => (T)target.GetType().GetField(field,Private).GetValue(target);
    static object Call(object target,string method,params object[] args) => target.GetType().GetMethod(method,Private).Invoke(target,args);
    public static void Run()
    {
        PortalRayTrialCheck.Run();
        PassthroughTrialCheck.Run();
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        UnityEngine.Object.FindObjectOfType<PortalManager>().BuildPortal();
        var marker=new GameObject("ContinuousPreviewCheck").AddComponent<DoorCornerMarker>();Call(marker,"Start");Call(marker,"Begin");
        var setter=typeof(PicoPassthroughSetup).GetProperty("IsReady").GetSetMethod(true);
        bool previousReady=PicoPassthroughSetup.IsReady;
        setter.Invoke(null,new object[]{true});
        try
        {
            Set(marker,"_firstRay",new Ray(new Vector3(-.3f,1,2),Vector3.back));Set(marker,"_hasFirstRay",true);
            for(int i=-100;i<=100;i++)
            {
                var hand=new PortalControllerInput.Hand { tracked=true,position=new Vector3(.3f,1.2f,2),rotation=Quaternion.Euler(0,180+i*.2f,0) };
                Call(marker,"UpdateRay",hand);
                Require(Get<bool>(marker,"_rayHit")&&Get<bool>(marker,"_rayFresh"),"marker preview gate returned at "+i);
                foreach(string name in new[]{"TwoRayIntersection","NearestPointOnFirstRay","NearestPointOnSecondRay"})
                    Require(marker.transform.Find(name).gameObject.activeSelf,"visible nearest marker disappeared at "+i);
                Require(marker.transform.Find("ClosestPointBridge").GetComponent<LineRenderer>().enabled,"distance connector disappeared");
            }
            var before=Get<DoorRayIntersection.Solution>(marker,"_solution");
            Call(marker,"UpdateRay",default(PortalControllerInput.Hand));
            Require(Get<bool>(marker,"_rayHit")&&!Get<bool>(marker,"_rayFresh"),"lost tracking must freeze preview but prohibit stale capture");
            Require(Get<DoorRayIntersection.Solution>(marker,"_solution").point==before.point,"tracking loss moved frozen point");
            Require(marker.transform.Find("TwoRayIntersection").gameObject.activeSelf,"tracking loss hid point");
            Call(marker,"Undo");Call(marker,"UpdateRay",default(PortalControllerInput.Hand));
            Require(!Get<bool>(marker,"_rayHit")&&!marker.transform.Find("TwoRayIntersection").gameObject.activeSelf,"undo retained a stale candidate");
        }
        finally { setter.Invoke(null,new object[]{previousReady}); }
        File.WriteAllText("Builds/controller-check/continuous-result.txt","PASS: 201 actual marker updates retain endpoints/midpoint/connector; tracking loss freezes without allowing stale capture; undo removes old candidate. Mathematical sweep, actual controller layouts, guide rendering and transparent background render checks passed. Physical passthrough requires headset verification.\n");
        Debug.Log("[ContinuousRayTrialCheck] ALL CHECKS PASSED");
    }
}
