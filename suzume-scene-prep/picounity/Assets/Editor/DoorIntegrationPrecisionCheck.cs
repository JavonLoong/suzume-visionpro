using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;

public static class DoorIntegrationPrecisionCheck
{
    const string Folder="D:/suzume-integration-20261127";
    static readonly System.Random Random=new System.Random(20261127);
    static readonly List<string> Report=new List<string>();
    static void Require(bool ok,string why){if(!ok)throw new Exception(why);}
    static float Noise(float sigma)=>sigma*(float)(Math.Sqrt(-2*Math.Log(1-Random.NextDouble()))*Math.Cos(2*Math.PI*Random.NextDouble()));
    static DoorPoseSolver.Observation Observe(Vector3 door,Quaternion rotation,float w,float h,Vector3 eye,float time,float sigma)
    {
        var centre=door+rotation*Vector3.up*h*.5f;
        var o=new DoorPoseSolver.Observation{cameraToWorld=Matrix4x4.TRS(eye,Quaternion.LookRotation(centre-eye,Vector3.up),Vector3.one),fx=1302,fy=1302,cx=1023.5f,cy=767.5f,time=time};
        var corners=DoorQuadPlacement.Rectangle(door,rotation,w,h);var pixels=new Vector2[4];
        for(int i=0;i<4;i++){var p=o.cameraToWorld.inverse.MultiplyPoint3x4(corners[i]);pixels[i]=new Vector2(o.fx*p.x/p.z+o.cx+Noise(sigma),o.cy-o.fy*p.y/p.z+Noise(sigma));}
        o.SetPixels(pixels);return o;
    }
    static float Rms(IList<DoorPoseSolver.Observation> observations,DoorPoseSolver.Solution pose,float w,float h)
    {
        double sum=0;var corners=DoorQuadPlacement.Rectangle(pose.position,pose.rotation,w,h);
        foreach(var o in observations)foreach(int k in new[]{0,1,2,3})
        {var p=o.cameraToWorld.inverse.MultiplyPoint3x4(corners[k]);var pixel=new Vector2(o.fx*p.x/p.z+o.cx,o.cy-o.fy*p.y/p.z);sum+=(pixel-o.Pixel(k)).sqrMagnitude;}
        return (float)Math.Sqrt(sum/(observations.Count*8));
    }
    static DoorPoseSolver.Solution OldAverage(List<DoorPoseSolver.Observation> views,float w,float h)
    {
        var s=new DoorPoseSolver.Solution();Vector3 forward=Vector3.zero,up=Vector3.zero;
        foreach(var o in views){Require(DoorPoseSolver.SolveSingle(o,w,h,out var p),"single-view initialization failed");s.position+=p.position/views.Count;forward+=p.rotation*Vector3.forward;up+=p.rotation*Vector3.up;s.rmsPixels+=p.rmsPixels/views.Count;}
        s.rotation=Quaternion.LookRotation(forward,up);return s;
    }
    static float Median(List<float> values){values.Sort();return values[values.Count/2];}
    static void Geometry()
    {
        var oldError=new List<float>();var newError=new List<float>();var times=new List<float>();
        for(int trial=0;trial<36;trial++)
        {
            float w=DoorPhysicalSize.Presets[trial%3].width,h=DoorPhysicalSize.Presets[trial%3].height;
            var position=new Vector3(trial%2==0?.3f:12.3f,.75f,.5f);
            var rotation=Quaternion.Euler((trial%4-1)*8,17+trial%6*9,(trial%3-1)*6);
            var views=new List<DoorPoseSolver.Observation>();
            for(int i=0;i<12;i++)
            {
                var eye=position+rotation*(new Vector3((i-5.5f)*.012f,h*.5f+.03f,trial%2==0?.35f:.65f));
                views.Add(Observe(position,rotation,w,h,eye,i*.15f,trial<3?0:.5f));
            }
            var old=OldAverage(views,w,h);var clock=System.Diagnostics.Stopwatch.StartNew();
            Require(DoorPoseSolver.SolveMultiView(views,w,h,old,out var joint),"joint fit failed");clock.Stop();
            float actual=Rms(views,joint,w,h);
            Require(Mathf.Abs(actual-joint.rmsPixels)<.01f,"reported residual is not final-pose error");
            Require(actual<=Rms(views,old,w,h)+.02f,"joint fit made reprojection worse");
            if(trial<3)Require(Vector3.Distance(position,joint.position)<.0001f&&Quaternion.Angle(rotation,joint.rotation)<.1f,"exact tilted geometry mismatch");
            oldError.Add(Vector3.Distance(position,old.position)*1000);newError.Add(Vector3.Distance(position,joint.position)*1000);times.Add((float)clock.Elapsed.TotalMilliseconds);
            Report.Add($"case={trial} old_position_mm={oldError[trial]:F4} joint_position_mm={newError[trial]:F4} actual_rms_px={actual:F4} reported_rms_px={joint.rmsPixels:F4}");
        }
        Require(Median(newError)<Median(oldError),"joint fit did not improve position median");
        Report.Add($"36 synthetic multi-view cases: old median={Median(oldError):F4}mm joint median={Median(newError):F4}mm; solve median={Median(times):F3}ms on PC, NOT headset/field accuracy.");
        float width=.023f,height=.0558f;var centre=new Vector3(.1f,.7f,.4f);var eyeFixed=centre+new Vector3(0,.03f,.4f);
        var bad=new List<DoorPoseSolver.Observation>();var stabilizer=new DoorPoseStabilizer{assumeUpright=false};
        for(int i=0;i<16;i++)
        {
            var o=Observe(centre,Quaternion.identity,width,height,eyeFixed,i*.15f,0);
            var points=new Vector2[4];for(int j=0;j<4;j++)points[j]=o.Pixel(j)+new Vector2(i%2==0?14:-14,0);o.SetPixels(points);bad.Add(o);
            Require(stabilizer.Add(o,width,height)!=DoorPoseStabilizer.Event.Locked,"inconsistent views falsely locked");
        }
        var oldBad=OldAverage(bad,width,height);Require(DoorPoseSolver.SolveMultiView(bad,width,height,oldBad,out var fittedBad),"conflict diagnostic fit failed");
        Require(oldBad.rmsPixels<.01f&&fittedBad.rmsPixels>5,"failed to reproduce old falsely low residual");
        Report.Add($"Contradictory observations: old reported RMS={oldBad.rmsPixels:F4}px; joint reported RMS={fittedBad.rmsPixels:F4}px; correctly refused lock.");
        var fresh=new DoorPoseStabilizer{assumeUpright=false};var valid=bad[0];fresh.Add(valid,width,height);
        for(int i=0;i<20;i++)fresh.Add(valid,width,height);Require(fresh.ObservationCount==1,"same camera timestamp counted repeatedly");
        var invalid=valid;invalid.time=1;invalid.fx=float.NaN;fresh.Add(invalid,width,height);Require(fresh.ObservationCount==1,"invalid intrinsics polluted window");
        invalid=valid;invalid.time=1;invalid.cameraToWorld=Matrix4x4.zero;Require(!DoorPoseSolver.SolveSingle(invalid,width,height,out _),"singular camera pose accepted");
        fresh.Reset();valid.time=0;fresh.Add(valid,width,height);Require(fresh.ObservationCount==1,"reset retained stale clock");
    }
    static void Deadlines()
    {
        var p=new DoorBleProtocol();var sent=new List<string>();p.Transmit+=sent.Add;
        p.Connected(0);p.Feed("R,1,1,1500\n",2.51);Require(!p.CanAct&&p.State==DoorBleProtocol.Phase.Fault,"late R revived expired query");
        p.Connected(0);p.Feed("R,1,1,1500\n",.1);p.Request('O',1);p.Feed("A,2,2167\n",3.51);Require(p.State==DoorBleProtocol.Phase.Fault,"late A revived expired request");
        p.Connected(0);p.Feed("R,1,1,1500\n",.1);p.Request('O',1);p.Feed("A,2,2167\n",1.1);int count=sent.Count;
        p.Feed("D,2,2145\n",13.11);Require(!p.CanAct&&p.State==DoorBleProtocol.Phase.Fault&&sent.Count==count,"late D claimed completion or replayed movement");
        p.Connected(20);Require(sent[sent.Count-1]=="Q,1\n","reconnection must query only");
        Report.Add("BLE: delayed R/A/D cannot revive expired commands; no automatic motion resend; reconnection queries only.");
    }
    public static void Run()
    {
        Directory.CreateDirectory(Folder);Geometry();Deadlines();
        PhysicalDoorTrialCheck.Run();
        File.WriteAllLines(Folder+"/joint-pose-and-ble-check.txt",Report);
        Debug.Log("[DoorIntegrationPrecisionCheck] ALL CHECKS PASSED\n"+string.Join("\n",Report));
    }
}
