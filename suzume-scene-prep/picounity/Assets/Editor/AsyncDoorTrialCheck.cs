using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Unity.Barracuda;
using UnityEngine;

public static class AsyncDoorTrialCheck
{
    static void Require(bool ok,string why) { if(!ok)throw new Exception(why); }
    static void Drain(IEnumerator root,Action step=null)
    {
        var stack=new Stack<IEnumerator>();stack.Push(root);
        var timeout=System.Diagnostics.Stopwatch.StartNew();
        while(stack.Count>0)
        {
            if(timeout.Elapsed.TotalSeconds>30)throw new Exception("async test timed out");
            var current=stack.Peek();
            if(!current.MoveNext()){(current as IDisposable)?.Dispose();stack.Pop();continue;}
            if(current.Current is IEnumerator nested)stack.Push(nested);
            else { step?.Invoke(); System.Threading.Thread.Sleep(1); }
        }
    }
    static void UpsampleParity()
    {
        foreach (var scale in new[]{new[]{2,2},new[]{2,3},new[]{1,1}})
        foreach (int channels in new[]{1,3,48})
        {
            var values=new float[2*3*5*channels];
            for(int i=0;i<values.Length;i++)values[i]=(i%97-48)*.125f;
            using(var input=new Tensor(2,3,5,channels,values))
            {
                var burst=new BurstCPUOps();
                using(var output=burst.Upsample2D(input,scale,false))
                {
                    var actual=output.ToReadOnlyArray();
                    for(int b=0;b<2;b++)for(int y=0;y<3*scale[1];y++)
                    for(int x=0;x<5*scale[0];x++)for(int c=0;c<channels;c++)
                    {
                        int target=((b*3*scale[1]+y)*5*scale[0]+x)*channels+c;
                        int source=((b*3+y/scale[1])*5+x/scale[0])*channels+c;
                        Require(actual[target]==values[source],"nearest upsample changed a value");
                    }
                }
                burst.ResetAllocator(false);
            }
        }
        Debug.Log("[AsyncDoorTrialCheck] upsample exact copies PASS: 2 batches, 3 scales, 3 channel counts");
    }
    public static void Run()
    {
        UpsampleParity();
        string path="D:/suzume-door-fix-20261120/trial-1.12.5/000.pgm";
        byte[] bytes=File.ReadAllBytes(path);int offset=0;
        for(int i=0;i<3;i++)while(bytes[offset++]!=10){}
        var frame=new DoorCameraFrame{width=2048,height=1536,time=100,gray=new byte[2048*1536]};
        Buffer.BlockCopy(bytes,offset,frame.gray,0,frame.gray.Length);
        var crop=new Rect(748.38f,279.49f,623.01f,467.26f);
        using(var net=BarracudaDoorDetector.Create(WorkerFactory.Type.CSharpBurst))
        {
            var expected=new Vector2[4];var scores=new float[4];
            Require(net.TryDetectGuided(frame,crop,expected,scores),"sync reference failed");
            net.Reset();var points=new Vector2[4];var conf=new float[4];bool found=false;int yields=0;
            Drain(net.DetectGuidedAsync(frame,crop,points,conf,x=>found=x),()=>yields++);
            Require(found&&!net.IsRunning&&yields>2,"async did not finish or yield");
            for(int i=0;i<4;i++)Require(Vector2.Distance(points[i],expected[i])<.001f&&Mathf.Abs(conf[i]-scores[i])<.00001f,"async changed model result");
            foreach(bool retarget in new[]{true,false})
            {
                net.Reset();found=true;bool valid=true,invalidated=false;
                Drain(net.DetectGuidedAsync(frame,crop,points,conf,x=>found=x,()=>valid),()=>{
                    if(invalidated)return;invalidated=true;
                    if(retarget)net.Reset();else valid=false;
                });
                Require(invalidated&&!found&&!net.IsRunning,"late result survived reset/focus loss");
            }
            net.Reset();found=false;
            Drain(net.DetectGuidedAsync(frame,crop,points,conf,x=>found=x));
            Require(found&&!net.IsRunning,"cancel left worker unusable");
            Debug.Log($"[AsyncDoorTrialCheck] PASS: exact output parity, reset/focus invalidation, worker reuse, cooperative yields={yields}");
        }
    }
}
