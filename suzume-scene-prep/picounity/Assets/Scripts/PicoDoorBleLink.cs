using System;
using UnityEngine;
#if UNITY_ANDROID
using UnityEngine.Android;
#endif

public sealed class PicoDoorBleLink : MonoBehaviour
{
    public static PicoDoorBleLink Instance { get; private set; }
    public static bool Active => Instance!=null;
    public string Status { get; private set; } = "disconnected";
    public bool CanAct => protocol.CanAct && !writeInFlight && foreground && !paused;
    public string GuidePage => "ble_"+DisplayStatus(Status);
    readonly DoorBleProtocol protocol=new DoorBleProtocol();
    readonly DoorBleButtonGate buttons=new DoorBleButtonGate();
    bool foreground=true,paused,started,writeInFlight,permissionRequested;
    float retryAt,writeDeadline;
    string address="",lastLogged="";
#if UNITY_ANDROID && !UNITY_EDITOR
    AndroidJavaObject client;
#endif
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        // Independent trial package; formal and old applications keep their existing controls.
        if(!Application.isEditor && Application.platform==RuntimePlatform.Android && Application.identifier=="com.suzume.portal.bletrial")
            new GameObject("PhysicalDoorBle").AddComponent<PicoDoorBleLink>();
    }
    void Awake()
    {
        Instance=this;protocol.Transmit+=Transmit;
#if UNITY_ANDROID && !UNITY_EDITOR
        using(var unity=new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using(var activity=unity.GetStatic<AndroidJavaObject>("currentActivity"))
        using(var intent=activity.Call<AndroidJavaObject>("getIntent"))
        {
            // Explicit bench-only address. No board address is compiled into the APK.
            address=intent.Call<string>("getStringExtra","com.suzume.door.BOARD_ADDRESS")??"";
            client=new AndroidJavaObject("com.suzume.door.DoorBleClient",activity);
        }
#endif
    }
    bool PermissionsReady()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        int sdk;using(var version=new AndroidJavaClass("android.os.Build$VERSION"))sdk=version.GetStatic<int>("SDK_INT");
        string[] required=sdk>=31?new[]{"android.permission.BLUETOOTH_SCAN","android.permission.BLUETOOTH_CONNECT"}:new[]{Permission.FineLocation};
        bool granted=true;foreach(var p in required)granted&=Permission.HasUserAuthorizedPermission(p);
        if(!granted&&!permissionRequested){permissionRequested=true;Permission.RequestUserPermissions(required);}
        return granted;
#else
        return false;
#endif
    }
    void Update()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        if(client==null||!foreground||paused)return;
        if(!PermissionsReady()){Status="permission";return;}
        if(!started&&Time.unscaledTime>=retryAt){started=true;Status="connecting";client.Call("start",address);}
        for(int i=0;i<32;i++)
        {
            string ev=client.Call<string>("poll");if(string.IsNullOrEmpty(ev))break;
            int split=ev.IndexOf('|');if(split<0)continue;string kind=ev.Substring(0,split),value=ev.Substring(split+1);
            if(kind=="ready"){protocol.Connected(Time.unscaledTime);Status=protocol.Status;}
            else if(kind=="written")writeInFlight=false;
            else if(kind=="data") { Debug.Log("[DoorBLE] RX "+value.TrimEnd('\n'));protocol.Feed(value,Time.unscaledTime);Status=protocol.Status; }
            else if(kind=="state")Status=value;
            else if(kind=="error") { Fail(value);break; }
        }
        if(writeInFlight&&Time.unscaledTime>=writeDeadline)protocol.TransportError("write_timeout");
        protocol.Tick(Time.unscaledTime);
        if(protocol.State==DoorBleProtocol.Phase.Fault)Fail(protocol.Status);
        if(Status!=lastLogged){Debug.Log("[DoorBLE] status="+Status);lastLogged=Status;}
#endif
    }
    void LateUpdate()
    {
        var marker=DoorCornerMarker.Instance;
        var right=PortalControllerInput.Read(true);
        bool eligible=marker!=null&&marker.CanControlPhysicalDoor&&right.tracked&&CanAct;
        char command=buttons.Step(eligible,right.primary,right.secondary);
        if(command!='\0') { protocol.Request(command,Time.unscaledTime);Status=protocol.Status; }
    }
    void Transmit(string command)
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        writeInFlight=true;writeDeadline=Time.unscaledTime+3f;
        if(client==null||!client.Call<bool>("send",command)){protocol.TransportError("write_rejected");writeInFlight=false;}
        else Debug.Log("[DoorBLE] TX "+command.TrimEnd('\n'));
#endif
    }
    void Fail(string reason)
    {
        Close();Status=reason;retryAt=Time.unscaledTime+5f;
        // UNCAl/READ/protocol errors still reconnect with Q only, never replay O or C.
        Debug.LogWarning("[DoorBLE] "+reason+"; invalidate session, next connection queries only");
    }
    void Close()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        client?.Call("close");
#endif
        protocol.Disconnect();buttons.Reset();started=false;writeInFlight=false;
    }
    void OnApplicationPause(bool value){paused=value;if(value){Close();Status="paused";}}
    void OnApplicationFocus(bool value){foreground=value;if(!value){Close();Status="paused";}}
    void OnDestroy(){Close();protocol.Transmit-=Transmit;if(Instance==this)Instance=null;
#if UNITY_ANDROID && !UNITY_EDITOR
        client?.Dispose();client=null;
#endif
    }
    public static string DisplayStatus(string status)
    {
        switch(status)
        {
            case "ready":case "opened":case "closed":case "opening":case "closing":case "scanning":case "connecting":
            case "permission":case "query":case "UNCAL":case "READ":case "POSITION":case "UART":case "bluetooth_off":case "scan_timeout":return status;
            case "opening_request":case "closing_request":return "sending";
            default:return "disconnected";
        }
    }
}
