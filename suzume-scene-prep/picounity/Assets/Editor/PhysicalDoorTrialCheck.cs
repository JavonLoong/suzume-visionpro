using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class PhysicalDoorTrialCheck
{
    const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
    static void Require(bool ok,string why){if(!ok)throw new Exception(why);}
    static object Call(object target,string name,params object[] args)=>target.GetType().GetMethod(name,Private).Invoke(target,args);
    static T Get<T>(object target,string name)=>(T)target.GetType().GetField(name,Private).GetValue(target);
    static void Set(object target,string name,object value)=>target.GetType().GetField(name,Private).SetValue(target,value);
    public static void Run()
    {
        Protocol();ColdStart();
        // Existing checks include actual PICO input layout and all four corners / six directions.
        string original=Directory.GetCurrentDirectory();
        try
        {
            // Existing network fixtures are next to the real project; an optional path resolves local junctions.
            Directory.SetCurrentDirectory(Environment.GetEnvironmentVariable("SUZUME_SOURCE_PROJECT")??Path.GetFullPath(Path.Combine(Application.dataPath,"..")));
            DoorAdjustmentTrialCheck.Run();
        }
        finally { Directory.SetCurrentDirectory(original); }
        Directory.CreateDirectory("Builds/physical-door-check");
        File.WriteAllText("Builds/physical-door-check/result.txt",
            "PASS: empty/short/long/nonfinite arrays, reset to original mesh, serialized cold start, Ready UI, tracked left X into Collect, valid corner warp, Browse A/B ownership, LF fragments, matched R/A/D, stale and duplicate responses, errors, deadlines, reconnect query only, release-before-press gate, plus existing four-corner/controller regression. PC only; no headset or physical motor actuation.\n");
        Debug.Log("[PhysicalDoorTrialCheck] ALL CHECKS PASSED");
    }
    public static void BuildSeparateTrial(){Run();BuildPicoApk.BuildSeparateTrial();}
    public static void RenderColdStartCheck(){ColdStart();Debug.Log("[PhysicalDoorTrialCheck] cold-start UI PASS (simulated passthrough readiness)");}
    static void ColdStart()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal=UnityEngine.Object.FindObjectOfType<PortalManager>();portal.BuildPortal();
        var sample=new Vector3(.1f,.2f,.03f);
        var invalid=new List<Vector3[]> {null,Array.Empty<Vector3>(),new Vector3[1],new Vector3[2],new Vector3[3],new Vector3[4],new Vector3[5],
            new[]{new Vector3(float.NaN,0,0),Vector3.zero,Vector3.up,Vector3.one}};
        var warp=portal.GetComponent<PortalQuadWarp>()??portal.gameObject.AddComponent<PortalQuadWarp>();
        var filter=portal.transform.Find("PortalMask").GetComponentInChildren<MeshFilter>(true);var original=filter.sharedMesh;
        foreach(var points in invalid)
        {
            Require(DoorQuadPlacement.Warp(sample,points)==sample,"invalid Warp must preserve input");
            portal.adjustedOpening=points;portal.UpdatePortalState();Require(portal.adjustedOpening==null,"invalid quad not normalized");
            portal.SetWorldCorners(points);Require(portal.GetWorldCorners().Length==4,"default rectangle unavailable");
            warp.Apply(points);Require(filter.sharedMesh==original,"invalid input changed mesh");
        }
        var valid=DoorQuadPlacement.Rectangle(Vector3.zero,Quaternion.identity,PortalConfig.BaseDoorWidth,PortalConfig.BaseDoorHeight);
        valid[3]+=new Vector3(.01f,.02f,.03f);warp.Apply(valid);
        Require(filter.sharedMesh!=original,"valid corners did not warp mesh");
        portal.adjustedOpening=Array.Empty<Vector3>();portal.UpdatePortalState();Require(filter.sharedMesh==original,"old warp not reset");
        // Reproduce Unity's unset serialized-array state before Start, not only a hand-made nonempty quad.
        JsonUtility.FromJsonOverwrite("{\"adjustedOpening\":[]}",portal);
        var marker=new GameObject("ColdStartMarker").AddComponent<DoorCornerMarker>();
        Call(marker,"UpdateRay",new PortalControllerInput.Hand()); // partial initialization must be harmless
        Call(marker,"Start");Require(marker.IsInitialized&&marker.ProgressSummary.Contains("Ready"),"cold Start failed");
        var guide=Get<PortalGuideView>(marker,"_guide");Require(guide!=null,"Ready guide missing");
        guide.Show("ready",true,false,PortalGuideView.Context.Ready);
        Require(Get<Renderer>(guide,"_card").sharedMaterial.mainTexture!=null,"Ready guide has no text texture");
        SavePreview(Camera.main,"ready");
        var r=new PortalControllerInput.Hand{tracked=true,rotation=Quaternion.identity};var l=r;
        var setter=typeof(PicoPassthroughSetup).GetProperty("IsReady").GetSetMethod(true);bool wasReady=PicoPassthroughSetup.IsReady;
        try
        {
            // The PC has no headset passthrough. Simulate its ready signal to inspect the manual-step card.
            setter.Invoke(null,new object[]{true});
            Call(marker,"ProcessInput",r,l);l.primary=true;Call(marker,"ProcessInput",r,l);
            Require(marker.ProgressSummary.Contains("Collect"),"tracked left X failed to enter manual placement");
            SavePreview(Camera.main,"manual-placement");
        }
        finally {setter.Invoke(null,new object[]{wasReady});}
        var link=new GameObject("BrowseOwnership").AddComponent<PicoDoorBleLink>();Call(link,"Awake");
        Set(marker,"_mode",Enum.Parse(typeof(DoorCornerMarker).GetNestedType("Mode",BindingFlags.NonPublic),"Browse"));
        l.primary=false;r.primary=r.secondary=false;Call(marker,"ProcessInput",r,l);
        bool scene=Get<bool>(marker,"_selectedMountain"),help=Get<bool>(marker,"_help");
        r.primary=true;Call(marker,"ProcessInput",r,l);r.primary=false;r.secondary=true;Call(marker,"ProcessInput",r,l);
        Require(scene==Get<bool>(marker,"_selectedMountain")&&help==Get<bool>(marker,"_help"),"Browse A/B still trigger old shortcuts");
        UnityEngine.Object.DestroyImmediate(link.gameObject);UnityEngine.Object.DestroyImmediate(marker.gameObject);
        if(guide!=null)UnityEngine.Object.DestroyImmediate(guide.gameObject);
    }
    static void SavePreview(Camera camera,string name)
    {
        Directory.CreateDirectory("Builds/physical-door-check");
        var rt=new RenderTexture(1200,800,24);camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;
        var image=new Texture2D(1200,800,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,1200,800),0,0);image.Apply();
        File.WriteAllBytes("Builds/physical-door-check/"+name+".png",image.EncodeToPNG());
        camera.targetTexture=null;RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(image);UnityEngine.Object.DestroyImmediate(rt);
    }
    static void Protocol()
    {
        var p=new DoorBleProtocol();var sent=new List<string>();p.Transmit+=sent.Add;
        p.Connected(0);Require(sent[0]=="Q,1\n"&&!p.CanAct,"connection must query, not move");
        p.Feed("R,0,1,1500\nR,2,1,1500\nR,1,1,15",.1);Require(!p.CanAct,"stale or partial query accepted");
        p.Feed("00\n",.2);Require(p.CanAct,"fragmented query response rejected");
        Require(p.Request('O',1)&&sent[1]=="O,2\n","open request encoding");
        Require(!p.Request('C',1)&&!p.CanAct,"parallel action allowed");
        p.Feed("A,2,2167\nA,2,2167\n",1.1);Require(p.State==DoorBleProtocol.Phase.Moving&&!p.CanAct,"A incorrectly completed movement");
        p.Feed("D,9,2145\n",1.2);Require(!p.CanAct,"wrong sequence completed movement");
        p.Feed("D,2,2145\nD,2,2145\n",1.3);Require(p.CanAct&&p.Status=="opened"&&p.Position==2145,"matched D did not finish");
        Require(p.Request('C',2),"reset request refused");p.Feed("A,3,1500\nD,3,1519\n",2.1);Require(p.Status=="closed","reset not completed");
        p.Disconnect();p.Feed("D,3,1519\n",3);Require(!p.CanAct,"disconnected response accepted");
        int count=sent.Count;p.Connected(4);Require(sent.Count==count+1&&sent[sent.Count-1]=="Q,1\n","reconnection replayed motion");
        p.Feed("R,1,1,1500\n",4.1);p.Request('O',5);p.Feed("D,2,2145\n",5.1);Require(p.State==DoorBleProtocol.Phase.Fault,"D before A accepted");
        foreach(string reply in new[]{"R,1,0,1500\n","R,1,1,-1\n","R,1,1,2501\n","E,0,BUSY\n","R,1,1,1500\r\n",new string('x',129)})
        {p.Connected(0);p.Feed(reply,.1);Require(p.State==DoorBleProtocol.Phase.Fault&&!p.CanAct,"bad response accepted: "+reply);}
        foreach(string reason in new[]{"UNCAL","READ","POSITION","UART","BAD","SEQ","BUSY"})
        {p.Connected(0);p.Feed("R,1,1,1500\n",.1);p.Request('O',.2);p.Feed("E,2,"+reason+"\n",.3);Require(!p.CanAct&&p.Status==reason,"action error ignored");}
        p.Connected(0);p.Tick(3);Require(p.State==DoorBleProtocol.Phase.Fault,"Q timeout ignored");
        p.Connected(0);p.Feed("R,1,1,1500\n",.1);p.Request('O',1);count=sent.Count;p.Tick(4);Require(!p.CanAct&&sent.Count==count,"A timeout replayed action");
        p.Connected(0);p.Feed("R,1,1,1500\n",.1);p.Request('O',1);p.Feed("A,2,2167\n",1.1);p.Tick(14);Require(!p.CanAct,"D timeout accepted");
        var gate=new DoorBleButtonGate();
        Require(gate.Step(true,true,false)=='\0',"held A on entry fired");gate.Step(true,false,false);
        Require(gate.Step(true,true,false)=='O'&&gate.Step(true,true,false)=='\0',"held A repeated");
        gate.Step(false,false,false);Require(gate.Step(true,false,true)=='\0',"B on tune exit/track regain fired");
        gate.Step(true,false,false);Require(gate.Step(true,false,true)=='C',"new B edge missing");
        gate.Step(true,false,false);Require(gate.Step(true,true,true)=='\0',"simultaneous A/B fired");
        Debug.Log("[PhysicalDoorTrialCheck] protocol and press-release guards PASS");
    }
}
