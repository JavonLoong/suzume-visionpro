using System;
using System.IO;
using System.Globalization;
using System.Linq;
using System.Text;
using Unity.Barracuda;
using UnityEngine;

public static class ScreenDoorReplayCheck
{
    static void Require(bool ok,string why){if(!ok)throw new Exception(why);}
    public static void Run()
    {
        var report=new StringBuilder("OFFLINE ONLY. Recorded monitor photos; repeated still images are not live tracking or independent validation.\n");
        TiltChecks(report);
        const string root="D:/suzume-ota-20261120/trial-1.12.4/";
        using(var detector=BarracudaDoorDetector.Create(WorkerFactory.Type.CSharpBurst))
        {
            Require(detector!=null,"network unavailable");
            for(int n=0;n<7;n++)
            {
                var file=File.ReadAllBytes(root+n.ToString("000")+".pgm");int offset=0;
                for(int line=0;line<3;line++)while(file[offset++]!=10){}
                var frame=new DoorCameraFrame{width=2048,height=1536,gray=new byte[2048*1536],fx=1302.441f,fy=1302.505f,cx=1023.5f,cy=767.5f,time=n*100};
                Buffer.BlockCopy(file,offset,frame.gray,0,frame.gray.Length);
                string text=File.ReadAllText(root+n.ToString("000")+".txt");
                var values=text.Substring(text.IndexOf("cameraToWorld ")+14).Split(new[]{' ','\r','\n'},StringSplitOptions.RemoveEmptyEntries);
                for(int i=0;i<16;i++)frame.cameraToWorld[i/4,i%4]=float.Parse(values[i],CultureInfo.InvariantCulture);
                var hint=new DoorSearchHint();hint.Set(n==0?new Ray(new Vector3(.234f,.929f,3.013f),new Vector3(.716f,.024f,-.698f)):new Ray(new Vector3(.241f,.910f,3.023f),new Vector3(.679f,.041f,-.733f)));
                var points=new Vector2[4];var scores=new float[4];int accepted=0,first=-1;
                for(int j=0;j<DoorSearchHint.SearchCycleLength;j++)
                {
                    detector.Reset();if(!hint.TryCrop(frame,.0558f,out var crop))continue;
                    if(!detector.TryDetectGuided(frame,crop,points,scores)||scores.Min()<.5f)continue;
                    var obs=new DoorPoseSolver.Observation{cameraToWorld=frame.cameraToWorld,fx=frame.fx,fy=frame.fy,cx=frame.cx,cy=frame.cy,time=frame.time};obs.SetPixels(points);
                    if(!DoorPoseSolver.SolveSingle(obs,.023f,.0558f,out var pose)||!hint.Accepts(pose.position+pose.rotation*Vector3.up*.0279f,.0558f))continue;
                    accepted++;if(first>=0)continue;first=j;
                    float pixels=Mathf.Max(Vector2.Distance(points[0],points[2]),Vector2.Distance(points[1],points[3]));
                    float threshold=Mathf.Max(1.5f,pixels*.02f);
                    var tilted=new DoorPoseStabilizer{assumeUpright=false,maximumRmsPixels=threshold};
                    var upright=new DoorPoseStabilizer{assumeUpright=true,maximumRmsPixels=threshold};
                    int lockedAt=-1;
                    for(int k=0;k<12;k++)
                    {
                        obs.time=frame.time+k*.22f;
                        if(tilted.Add(obs,.023f,.0558f)==DoorPoseStabilizer.Event.Locked)lockedAt=k+1;
                        upright.Add(obs,.023f,.0558f);
                    }
                    report.AppendLine($"frame={n:000} firstAcceptedCrop={j+1} fullRotationRms={tilted.Current.rmsPixels:F3}px uprightRms={upright.Current.rmsPixels:F3}px threshold={threshold:F3}px repeatedStillLockAt={lockedAt} uprightState={upright.CurrentState}");
                    Require(tilted.CurrentState==DoorPoseStabilizer.State.Locked,"full-rotation repeated-frame lock failed: "+n);
                }
                report.AppendLine($"frame={n:000} acceptedCrops={accepted}/{DoorSearchHint.SearchCycleLength}");
                Require(n<5?accepted>0:accepted==0,"recorded positive/negative regression: "+n);
            }
        }
        File.WriteAllText("D:/suzume-door-tuning-20261120/screen-replay-result.txt",report.ToString());
        Debug.Log("[ScreenDoorReplayCheck] PASS\n"+report);
    }
    static void TiltChecks(StringBuilder report)
    {
        int cases=0;float maxPosition=0,maxAngle=0;double maximumWorkMs=0;
        foreach(float pitch in new[]{-25f,-10f,12f,30f})foreach(float yaw in new[]{-45f,35f})
        foreach(float height in new[]{.0558f,.3f})foreach(float distance in new[]{.25f,.5f,.8f})
        {
            float width=height*.023f/.0558f;var bottom=new Vector3(.2f,.7f,.3f);var rotation=Quaternion.Euler(pitch,yaw,13f);
            var points=DoorQuadPlacement.Rectangle(bottom,rotation,width,height);
            var state=new DoorPoseStabilizer{assumeUpright=false};
            for(int step=0;step<10;step++)
            {
                var centre=bottom+rotation*Vector3.up*height*.5f;
                var eye=centre+rotation*new Vector3(Mathf.Sin(step)*.02f,.04f,distance);
                var camera=Matrix4x4.TRS(eye,Quaternion.LookRotation(centre-eye,Vector3.up),Vector3.one);
                var obs=new DoorPoseSolver.Observation{cameraToWorld=camera,fx=1302,fy=1302,cx=1024,cy=768,time=step*.22f};
                var px=new Vector2[4];for(int i=0;i<4;i++){var p=camera.inverse.MultiplyPoint3x4(points[i]);px[i]=new Vector2(obs.fx*p.x/p.z+obs.cx,obs.cy-obs.fy*p.y/p.z);}
                obs.SetPixels(px);var watch=System.Diagnostics.Stopwatch.StartNew();
                var worker=state.Snapshot();worker.Add(obs,width,height);state.CopyFrom(worker);watch.Stop();maximumWorkMs=Math.Max(maximumWorkMs,watch.Elapsed.TotalMilliseconds);
            }
            Require(state.CurrentState==DoorPoseStabilizer.State.Locked,"tilted synthetic pose failed to lock");
            float error=Vector3.Distance(bottom,state.LockedSolution.position),angle=Quaternion.Angle(rotation,state.LockedSolution.rotation);
            Require(error<.001f&&angle<.5f,"tilted geometry mismatch");maxPosition=Mathf.Max(maxPosition,error);maxAngle=Mathf.Max(maxAngle,angle);cases++;
        }
        report.AppendLine($"Synthetic exact-projection cases={cases}; maxPositionMm={maxPosition*1000:F5}; maxRotationDeg={maxAngle:F5}; maxWorkerMathMsOnPC={maximumWorkMs:F2}. These are mathematical errors, not headset accuracy.");
    }
}
