using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Unity.XR.PXR;
using UnityEngine;

// Explicit adb diagnostic only. Uses its own temporary anchor and file, never the user's placement key.
public sealed class DoorShowcaseRuntimeProbe:MonoBehaviour
{
    [Serializable] class Record { public string uuid;public Vector3[] corners; }
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if(Application.platform!=RuntimePlatform.Android||Application.isEditor)return;
        using(var player=new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using(var activity=player.GetStatic<AndroidJavaObject>("currentActivity"))
        using(var intent=activity.Call<AndroidJavaObject>("getIntent"))
        {
            if(!intent.Call<bool>("getBooleanExtra","door_showcase_probe",false))return;
            intent.Call("removeExtra","door_showcase_probe");
        }
        new GameObject("ExplicitShowcaseProbe").AddComponent<DoorShowcaseRuntimeProbe>();
    }
    async void Start()
    {
        string path=Path.Combine(Application.persistentDataPath,"showcase_probe_anchor.json");ulong handle=0;bool keep=false,newPersisted=false;
        using(var timeout=new CancellationTokenSource(25000))
        try
        {
            for(int n=0;n<100;n++)
            {
                if(DoorCornerMarker.Instance!=null&&DoorCornerMarker.Instance.AnchorProviderReady)break;
                await Task.Delay(100,timeout.Token);
            }
            if(DoorCornerMarker.Instance==null||!DoorCornerMarker.Instance.AnchorProviderReady)throw new Exception("anchor provider unavailable");
            if(File.Exists(path))
            {
                var record=JsonUtility.FromJson<Record>(File.ReadAllText(path));
                var query=await PXR_MixedReality.QuerySpatialAnchorAsync(new[]{Guid.Parse(record.uuid)},timeout.Token);
                if(query.result!=PxrResult.SUCCESS)throw new Exception("query "+query.result);
                foreach(var candidate in query.anchorHandleList)
                {
                    if(PXR_MixedReality.GetAnchorUuid(candidate,out var uuid)==PxrResult.SUCCESS&&uuid.ToString()==record.uuid)handle=candidate;
                    else PXR_MixedReality.DestroyAnchor(candidate);
                }
                if(handle==0)throw new Exception("persisted UUID not restored");
                if(PXR_MixedReality.LocateAnchor(handle,out var position,out var rotation)!=PxrResult.SUCCESS)throw new Exception("restored anchor could not locate");
                var world=DoorQuadPlacement.ToWorld(record.corners,PortalControllerInput.ToWorld(position),PortalControllerInput.ToWorld(rotation));
                if(!DoorQuadPlacement.TryFit(world,out _))throw new Exception("restored edited quad invalid");
                var roundTrip=DoorQuadPlacement.ToLocal(world,PortalControllerInput.ToWorld(position),PortalControllerInput.ToWorld(rotation));
                float error=0;for(int i=0;i<4;i++)error=Mathf.Max(error,Vector3.Distance(roundTrip[i],record.corners[i]));
                if(error>.00001f)throw new Exception("corner offset round-trip mismatch");
                var remove=await PXR_MixedReality.UnPersistSpatialAnchorAsync(handle,timeout.Token);
                if(remove!=PxrResult.SUCCESS)throw new Exception("temporary anchor cleanup "+remove);
                File.Delete(path);
                Debug.Log($"[DoorShowcaseProbe] RESTORE_PASS uuid={record.uuid} editedCorners=4 localRoundTripErrorMm={error*1000:F5} cleanup=PASS; this is anchor API persistence, not physical alignment accuracy");
            }
            else
            {
                var cam=Camera.main;if(cam==null)throw new Exception("camera missing");
                var bottom=cam.transform.position+cam.transform.forward*.4f-Vector3.up*.03f;
                var rotation=Quaternion.LookRotation(-cam.transform.forward,Vector3.up);
                var corners=DoorQuadPlacement.Rectangle(bottom,rotation,.024f,.056f);
                corners[3]+=rotation*new Vector3(.001f,.001f,.002f);
                var create=await PXR_MixedReality.CreateSpatialAnchorAsync(PortalControllerInput.ToTracking(bottom),PortalControllerInput.ToTracking(rotation),timeout.Token);
                handle=create.anchorHandle;if(create.result!=PxrResult.SUCCESS||handle==0)throw new Exception("create "+create.result);
                var persist=await PXR_MixedReality.PersistSpatialAnchorAsync(handle,timeout.Token);
                if(persist!=PxrResult.SUCCESS)throw new Exception("persist "+persist);
                newPersisted=true;
                File.WriteAllText(path,JsonUtility.ToJson(new Record{uuid=create.uuid.ToString(),corners=DoorQuadPlacement.ToLocal(corners,bottom,rotation)}));
                keep=true;Debug.Log($"[DoorShowcaseProbe] PERSIST_PASS uuid={create.uuid} editedCorners=4; restart app with same probe flag to verify restore and clean up");
            }
        }
        catch(Exception e){Debug.LogError("[DoorShowcaseProbe] FAILED "+e.Message);}
        finally
        {
            if(newPersisted&&!keep&&handle!=0)
            {
                using(var cleanup=new CancellationTokenSource(3000))
                try{await PXR_MixedReality.UnPersistSpatialAnchorAsync(handle,cleanup.Token);}
                catch(Exception e){Debug.LogWarning("[DoorShowcaseProbe] incomplete temporary-anchor cleanup: "+e.Message);}
            }
            // A persisted stage-one handle is released but its storage remains for the restart test.
            if(handle!=0)PXR_MixedReality.DestroyAnchor(handle);
            if(!keep)Debug.Log("[DoorShowcaseProbe] diagnostic finished");
            if(this!=null)Destroy(gameObject);
        }
    }
}
