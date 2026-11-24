using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Unity.Barracuda;
using UnityEngine;

// Replays captured headset frames; this reports failures, not a claim of successful field recognition.
public static class RecordedDoorTrialCheck
{
    public static void Run()
    {
        const string root = "D:/suzume-ota-20261120/trial-1.12.4/";
        var report = new StringBuilder("Recorded real-camera replay, new detector.\nManual controls are explicitly selected regions, NOT automatic success.\n");
        using (var detector = BarracudaDoorDetector.Create(WorkerFactory.Type.CSharpBurst))
        {
            if (detector == null) throw new Exception("detector unavailable");
            for (int n=0;n<7;n++)
            {
                byte[] file=File.ReadAllBytes(root+n.ToString("000")+".pgm");
                int offset=0;for(int line=0;line<3;line++){while(file[offset++]!=10){}}
                var frame=new DoorCameraFrame{width=2048,height=1536,gray=new byte[2048*1536],fx=1302.441f,fy=1302.505f,cx=1023.5f,cy=767.5f,time=n*100};
                Buffer.BlockCopy(file,offset,frame.gray,0,frame.gray.Length);
                string text=File.ReadAllText(root+n.ToString("000")+".txt");
                var numbers=text.Substring(text.IndexOf("cameraToWorld ")+14).Split(new[]{' ','\r','\n'},StringSplitOptions.RemoveEmptyEntries);
                for(int i=0;i<16;i++)frame.cameraToWorld[i/4,i%4]=float.Parse(numbers[i],CultureInfo.InvariantCulture);
                var hint=new DoorSearchHint();hint.Set(n==0 ? new Ray(new Vector3(.234f,.929f,3.013f),new Vector3(.716f,.024f,-.698f)) : new Ray(new Vector3(.241f,.910f,3.023f),new Vector3(.679f,.041f,-.733f)));
                var pixels=new Vector2[4];var confidence=new float[4];int foundCount=0,passesFinal=0,poseAccepted=0;float best=0;
                for(int j=0;j<DoorSearchHint.SearchCycleLength;j++)
                {
                    detector.Reset();if(!hint.TryCrop(frame,.0558f,out var crop))continue;
                    bool found=detector.TryDetectGuided(frame,crop,pixels,confidence);
                    if(found){foundCount++;best=Mathf.Max(best,confidence.Min());if(confidence.Min()>=.5f){
                        passesFinal++;
                        var obs=new DoorPoseSolver.Observation{cameraToWorld=frame.cameraToWorld,fx=frame.fx,fy=frame.fy,cx=frame.cx,cy=frame.cy,time=frame.time};obs.SetPixels(pixels);
                        if(DoorPoseSolver.SolveSingle(obs,.023f,.0558f,out var pose)){
                            bool accepts=hint.Accepts(pose.position+pose.rotation*Vector3.up*.0279f,.0558f);if(accepts)poseAccepted++;
                            if(passesFinal==1){
                                var st=new DoorPoseStabilizer();DoorPoseStabilizer.Event change=DoorPoseStabilizer.Event.None;
                                for(int k=0;k<12;k++){obs.time=frame.time+k*.15f;change=st.Add(obs,.023f,.0558f);}
                                report.AppendLine($"frame {n:000} single RMS={pose.rmsPixels:F2}, rayAccepted={accepts}, uprightRms={st.Current.rmsPixels:F2}, fixed-image state={st.CurrentState}");
                            }
                        }
                    }}
                }
                report.AppendLine($"frame {n:000}: guided detections {foundCount}/{DoorSearchHint.SearchCycleLength}; all corners >=0.5: {passesFinal}; poseAccepted={poseAccepted}; best minimum score {best:F3}");
                if(n<5 && passesFinal==0)throw new Exception("Real door not detected: "+n);
                if(n>=5 && passesFinal>0)throw new Exception("Negative frame false positive: "+n);
                if(n==3)
                {
                    detector.Reset();bool found=detector.TryDetectGuided(frame,new Rect(795,370,800,600),pixels,confidence);
                    report.AppendLine("MANUAL CONTROL frame003: found="+found+" scores="+string.Join(",",confidence.Select(v=>v.ToString("F3",CultureInfo.InvariantCulture)))+"; final >=0.5="+(found&&confidence.Min()>=.5f));
                }
            }
        }
        File.WriteAllText("D:/suzume-door-fix-20261120/unity-recorded-replay.txt",report.ToString());
        Debug.Log("[RecordedDoorTrialCheck] "+report);
    }
}
