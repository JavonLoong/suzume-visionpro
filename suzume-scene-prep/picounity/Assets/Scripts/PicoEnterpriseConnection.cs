using System;
using System.Threading.Tasks;
using Unity.XR.PICO.TOBSupport;
using UnityEngine;

// The SDK has one bind callback per process. All app features must share that connection.
public static class PicoEnterpriseConnection
{
    static Task<bool> pending;
    static bool connected;
    public static bool IsConnected => connected;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Reset() { pending=null; connected=false; }

    public static Task<bool> EnsureAsync()
    {
        if(connected) return Task.FromResult(true);
        if(pending!=null && !pending.IsCompleted) return pending;
        var result=new TaskCompletionSource<bool>();
        pending=result.Task;
        try {
            if(!PXR_Enterprise.InitEnterpriseService(false)) result.TrySetResult(false);
            else PXR_Enterprise.BindEnterpriseService(ok => {
                connected=ok;
                result.TrySetResult(ok);
                Debug.Log("[PicoEnterprise] shared connection="+ok);
            });
        } catch(Exception e) {
            Debug.LogWarning("[PicoEnterprise] bind: "+e.Message);
            result.TrySetResult(false);
        }
        return pending;
    }

    public static void Disconnect()
    {
        if(pending==null) return;
        try { PXR_Enterprise.UnBindEnterpriseService(); }
        finally { pending=null; connected=false; }
    }
}
