using System;
using System.Collections;
using System.IO;
using System.Linq;
using Unity.Barracuda;
using UnityEngine;

// Explicit adb-only diagnostic. Does not place a door or accept controller input.
public class DoorDetectorRuntimeProbe : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if(Application.isEditor || Application.platform!=RuntimePlatform.Android)return;
        using(var player=new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using(var activity=player.GetStatic<AndroidJavaObject>("currentActivity"))
        using(var intent=activity.Call<AndroidJavaObject>("getIntent"))
        {
            if(!intent.Call<bool>("getBooleanExtra","door_detector_probe",false))return;
            intent.Call("removeExtra","door_detector_probe");
        }
        new GameObject("ExplicitDoorDetectorProbe").AddComponent<DoorDetectorRuntimeProbe>();
    }
    readonly System.Collections.Generic.List<float> frameTimes = new System.Collections.Generic.List<float>();
    bool measuring;
    void Update() { if (measuring) frameTimes.Add(Time.unscaledDeltaTime * 1000); }
    IEnumerator Start()
    {
        yield return new WaitForSecondsRealtime(3);
        string path=Path.Combine(Application.persistentDataPath,"door_detector_probe.pgm");
        if (!File.Exists(path)) { Debug.LogError("[DoorAsyncProbe] missing fixture"); yield break; }
        byte[] data=File.ReadAllBytes(path);int offset=0;
        for(int i=0;i<3;i++){while(data[offset++]!=10){}}
        if(data.Length-offset!=2048*1536) { Debug.LogError("[DoorAsyncProbe] invalid fixture"); yield break; }
        var frame=new DoorCameraFrame{width=2048,height=1536,gray=new byte[2048*1536],time=100};
        Buffer.BlockCopy(data,offset,frame.gray,0,frame.gray.Length);
        var crop=new Rect(748.38f,279.49f,623.01f,467.26f);
        var expected=new[]{new Vector2(1033.32f,643.18f),new Vector2(1069.64f,673.11f),new Vector2(1065.83f,491.61f),new Vector2(1112.28f,500.03f)};
        // Share the production worker; do not allocate a second network or change backend.
        var detector=DoorAutoLocator.Detector as BarracudaDoorDetector;
        if(detector==null) { Debug.LogError("[DoorAsyncProbe] no detector"); yield break; }
        for(int trial=0;trial<9;trial++)
        {
            if (DoorCornerMarker.Instance!=null && DoorCornerMarker.Instance.IsGuiding) break;
            while (detector.IsRunning) yield return null;
            detector.Reset();frame.time+=10;
            var points=new Vector2[4];var confidence=new float[4];bool found=false;
            var timer=System.Diagnostics.Stopwatch.StartNew();
            frameTimes.Clear();measuring=trial>0;
            yield return detector.DetectGuidedAsync(frame,crop,points,confidence,x=>found=x);
            measuring=false;timer.Stop();
            float error=0;for(int i=0;i<4;i++)error=Mathf.Max(error,Vector2.Distance(points[i],expected[i]));
            bool pass=found&&confidence.Min()>=.5f&&error<4;
            frameTimes.Sort();float p95=frameTimes.Count==0?0:frameTimes[(int)((frameTimes.Count-1)*.95f)];
            Debug.Log($"[DoorAsyncProbe] trial={trial} pass={pass} scores={string.Join(",",confidence.Select(v=>v.ToString("F3")))} maxError={error:F2}px totalMs={timer.Elapsed.TotalMilliseconds:F1} maxSliceMs={detector.MaximumSliceMilliseconds:F2} stage={detector.SlowestStage} sampleMs={detector.SamplingMilliseconds:F1} frames={frameTimes.Count} frameP95Ms={p95:F1} frameMaxMs={(frameTimes.Count>0?frameTimes.Last():0):F1}");
            yield return new WaitForSecondsRealtime(.25f);
        }
        detector.Reset();Debug.Log("[DoorAsyncProbe] COMPLETE");Destroy(gameObject);
    }
}
