using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Unity.Barracuda;

public static class DoorCornerRefinerCheck
{
    [Serializable] class Case {public string image,group;public int width,height;public float[] input,output,scores;public bool accepted;}
    [Serializable] class Cases {public Case[] cases;}
    const string Root="D:/suzume-integration-20261127/corner-refinement/";
    static void Require(bool ok,string why){if(!ok)throw new Exception(why);}
    static void Drain(IEnumerator root,Action step=null)
    {
        var stack=new Stack<IEnumerator>();stack.Push(root);var watch=System.Diagnostics.Stopwatch.StartNew();
        while(stack.Count>0)
        {
            Require(watch.Elapsed.TotalSeconds<30,"refiner coroutine timed out");var current=stack.Peek();
            if(!current.MoveNext()){(current as IDisposable)?.Dispose();stack.Pop();continue;}
            if(current.Current is IEnumerator nested)stack.Push(nested);else{step?.Invoke();System.Threading.Thread.Sleep(1);}
        }
    }
    static DoorCameraFrame Frame(Case item)=>new DoorCameraFrame{gray=File.ReadAllBytes(Root+"reference/"+item.image),width=item.width,height=item.height};
    static Vector2[] Points(float[] values){var points=new Vector2[4];for(int i=0;i<4;i++)points[i]=new Vector2(values[i*2],values[i*2+1]);return points;}
    const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
    static object Call(object target,string name,params object[] args)=>target.GetType().GetMethod(name,Private).Invoke(target,args);
    static void Set(object target,string name,object value)=>target.GetType().GetField(name,Private).SetValue(target,value);
    static T Get<T>(object target,string name)=>(T)target.GetType().GetField(name,Private).GetValue(target);
    sealed class SeedDetector:IDoorKeypointDetector,IDoorGuidedDetector
    {
        public Vector2[] seed;
        public void Reset(){}
        public bool TryDetect(DoorCameraFrame frame,Vector2[] pixels,float[] scores)=>false;
        public bool TryDetectGuided(DoorCameraFrame frame,Rect crop,Vector2[] pixels,float[] scores)
        {Array.Copy(seed,pixels,4);for(int i=0;i<4;i++)scores[i]=.9f;return true;}
    }
    static void Pipeline(NNModel asset,Case fixture)
    {
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal=UnityEngine.Object.FindObjectOfType<PortalManager>();portal.BuildPortal();
        var marker=new GameObject("CornerPipelineMarker").AddComponent<DoorCornerMarker>();Call(marker,"Start");
        var locator=new GameObject("CornerPipelineLocator").AddComponent<DoorAutoLocator>();Call(locator,"Awake");
        var old=DoorAutoLocator.Detector;var refiner=new DoorCornerRefiner(asset);Set(locator,"_cornerRefiner",refiner);
        var seed=Points(fixture.input);DoorAutoLocator.Detector=new SeedDetector{seed=seed};
        try
        {
            Set(marker,"_mode",Enum.Parse(typeof(DoorCornerMarker).GetNestedType("Mode",BindingFlags.NonPublic),"Guide"));
            var frame=Get<DoorCameraFrame>(locator,"_frame");frame.gray=File.ReadAllBytes(Root+"reference/"+fixture.image);
            frame.width=fixture.width;frame.height=fixture.height;frame.fx=frame.fy=1302;frame.cx=fixture.width*.5f;frame.cy=fixture.height*.5f;frame.cameraToWorld=Matrix4x4.identity;frame.time=Time.unscaledTime;
            var centre=(seed[0]+seed[1]+seed[2]+seed[3])*.25f;
            var ray=new Ray(Vector3.zero,new Vector3((centre.x-frame.cx)/frame.fx,(frame.cy-centre.y)/frame.fy,1));
            Require(locator.BeginGuided(ray)&&marker.CanRunGuided,"pipeline setup failed");
            Drain((IEnumerator)Call(locator,"ProcessFrame",marker,locator.hint.Revision));
            Require(Get<bool>(locator,"_refinementApplied"),"application pipeline did not use local refinement");
            var actual=Get<Vector2[]>(locator,"_pixels");var expected=Points(fixture.output);
            for(int i=0;i<4;i++)Require(Vector2.Distance(actual[i],expected[i])<.02f,"pipeline did not feed refined corners to pose fit");
            frame.time=Time.unscaledTime;Require(locator.BeginGuided(ray),"pipeline restart failed");bool cancelled=false;
            Drain((IEnumerator)Call(locator,"ProcessFrame",marker,locator.hint.Revision),()=>{if(!cancelled&&refiner.IsRunning){locator.CancelGuided();cancelled=true;}});
            Require(cancelled&&!Get<bool>(locator,"_refinementApplied"),"cancelled local result changed application points");
            for(int i=0;i<4;i++)Require(actual[i]==seed[i],"cancelled pipeline published local coordinates");
        }
        finally
        {DoorAutoLocator.Detector=old;UnityEngine.Object.DestroyImmediate(locator.gameObject);UnityEngine.Object.DestroyImmediate(marker.gameObject);}
    }
    public static void Run()
    {
        var asset=AssetDatabase.LoadAssetAtPath<NNModel>("Assets/Editor/CornerRefinementTrial/door_corner.onnx");
        if(asset==null)asset=Resources.Load<NNModel>("DoorNet/door_corner");
        Require(asset!=null,"local model missing");var fixtures=JsonUtility.FromJson<Cases>(File.ReadAllText(Root+"reference/reference.json"));
        var report=new List<string>();
        var unused=new DoorCornerRefiner(asset);unused.Dispose();unused.Dispose();
        using(var refiner=new DoorCornerRefiner(asset,WorkerFactory.Type.CSharpBurst))
        {
            float maxError=0,maxConfidence=0;int accepted=0;var times=new List<double>();Case acceptedCase=null;
            foreach(var item in fixtures.cases)
            {
                var frame=Frame(item);var result=new Vector2[4];var scores=new float[4];
                bool ok=refiner.TryRefine(frame,Points(item.input),result,scores);times.Add(refiner.LastMilliseconds);
                Require(ok==item.accepted,"acceptance parity failed "+item.image);
                if(ok){accepted++;acceptedCase=item;}
                var expected=Points(item.output);
                for(int i=0;i<4;i++)
                {
                    maxError=Mathf.Max(maxError,Vector2.Distance(result[i],expected[i]));
                    maxConfidence=Mathf.Max(maxConfidence,Mathf.Abs(scores[i]-item.scores[i]));
                    if(!ok)Require(result[i]==Points(item.input)[i],"rejected refinement changed original corner");
                }
            }
            Require(accepted>5&&maxError<.02f&&maxConfidence<.002f,"local model numerical parity failed");
            times.Sort();report.Add($"CPU Burst: fixtures={fixtures.cases.Length} acceptance matched all; accepted={accepted}; max coordinate difference={maxError:F6}px max confidence difference={maxConfidence:F6}; warm median inference={times[times.Count/2]:F3}ms on PC, not headset.");
            var f=Frame(acceptedCase);var p=Points(acceptedCase.input);var expectedPoints=Points(acceptedCase.output);var q=new Vector2[4];var c=new float[4];bool done=false;int yields=0;
            Drain(refiner.RefineAsync(f,p,q,c,x=>done=x,()=>true),()=>yields++);
            Require(done&&yields>0&&!refiner.IsRunning,"async refinement failed");
            report.Add($"Async PC sample: total={refiner.LastMilliseconds:F3}ms maximum main-thread slice={refiner.MaximumSliceMilliseconds:F3}ms; not headset latency.");
            for(int i=0;i<4;i++)Require(Vector2.Distance(q[i],expectedPoints[i])<.02f,"async output differs");
            bool valid=true;done=true;
            Drain(refiner.RefineAsync(f,p,q,c,x=>done=x,()=>valid),()=>valid=false);
            Require(!done&&!refiner.IsRunning,"cancelled refinement was published");
            Require(refiner.TryRefine(f,p,q,c),"cancelled worker cannot be reused");
            report.Add("PASS: sync/async agreement, cooperative yields, invalidation/cancel, worker reuse, all-original fallback.");
            Pipeline(asset,acceptedCase);report.Add("PASS: actual DoorAutoLocator pipeline feeds refined points into pose fitting; retarget/cancel during refinement cannot publish them.");
        }
        using(var cancelled=new DoorCornerRefiner(asset))
        {
            bool disposed=false,done=true;var item=fixtures.cases[0];
            Drain(cancelled.RefineAsync(Frame(item),Points(item.input),new Vector2[4],new float[4],x=>done=x,()=>true),()=>{if(!disposed){cancelled.Dispose();disposed=true;}});
            Require(disposed&&!done&&!cancelled.IsRunning,"dispose during preparation published a result");
        }
        File.WriteAllLines(Root+"unity-refiner-check.txt",report);foreach(var line in report)Debug.Log("[DoorCornerRefinerCheck] "+line);
    }
}
