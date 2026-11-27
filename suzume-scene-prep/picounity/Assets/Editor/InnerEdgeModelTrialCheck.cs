using System;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using Unity.Barracuda;

public static class InnerEdgeModelTrialCheck
{
    public static void Run()
    {
        const string root="D:/suzume-aperture-fit-20261125/reference/";
        var lines=File.ReadAllLines(root+"reference.txt");var report=new List<string>();
        foreach(var type in new[]{WorkerFactory.Type.CSharpBurst,WorkerFactory.Type.ComputePrecompiled})
        using(var detector=BarracudaDoorDetector.Create(type))
        {
            if(detector==null)throw new Exception("model failed to import into Unity");
            int agree=0,found=0;var differences=new List<float>();var watch=System.Diagnostics.Stopwatch.StartNew();
            foreach(var line in lines)
            {
                var s=line.Split(' ');int w=int.Parse(s[1]),h=int.Parse(s[2]);var bytes=File.ReadAllBytes(root+s[0]);
                int offset=0;for(int n=0;n<3;n++)while(bytes[offset++]!=10){}
                var frame=new DoorCameraFrame{width=w,height=h,gray=new byte[w*h],time=100};
                Buffer.BlockCopy(bytes,offset,frame.gray,0,w*h);var points=new Vector2[4];var confidence=new float[4];
                detector.Reset();bool ok=detector.TryDetect(frame,points,confidence);
                foreach(var c in confidence)ok&=c>=.5f;
                if(ok==(s[3]=="1"))agree++;
                if(ok&&s[3]=="1")
                {
                    found++;float error=0;
                    for(int i=0;i<4;i++)error=Mathf.Max(error,Vector2.Distance(points[i],new Vector2(float.Parse(s[4+i*2],CultureInfo.InvariantCulture),float.Parse(s[5+i*2],CultureInfo.InvariantCulture))));
                    differences.Add(error);
                }
            }
            watch.Stop();differences.Sort();
            if(differences.Count<15)throw new Exception("too few parity detections");
            float median=differences[differences.Count/2],p90=differences[(int)(differences.Count*.9f)];
            string row=$"{type}: cases={lines.Length}, agreement={agree}, matched positives={found}, median difference={median:F4}px, p90={p90:F4}px, elapsed={watch.Elapsed.TotalSeconds:F2}s (PC only)";
            report.Add(row);Debug.Log(row);
            if(agree<lines.Length-1||median>.3f||p90>1f)throw new Exception("Unity/Python model parity failed");
        }
        File.WriteAllLines("D:/suzume-aperture-fit-20261125/model-unity-check.txt",report);
        PhysicalApertureTrialCheck.Run();
        Debug.Log("[InnerEdgeModelTrialCheck] ALL CHECKS PASSED");
    }
}
