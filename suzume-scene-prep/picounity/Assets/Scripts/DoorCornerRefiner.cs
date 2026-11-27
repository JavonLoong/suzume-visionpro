using System;
using System.Collections;
using System.Threading.Tasks;
using Unity.Barracuda;
using UnityEngine;

// A small local network corrects an already detected inner opening. It cannot create detections.
// All four corners must agree with the confidence/movement policy, or all originals are retained.
public sealed class DoorCornerRefiner : IDisposable
{
    public const int Size=64;
    public const float MinimumConfidence=.5f;
    readonly IWorker worker;
    readonly float[] input=new float[4*Size*Size];
    readonly Vector2[] original=new Vector2[4],candidate=new Vector2[4];
    readonly byte[][] levels=new byte[6][];
    readonly int[] widths=new int[6],heights=new int[6];
    int levelCount;float scale,doorWidth;bool disposed,scheduled;
    public bool IsRunning {get;private set;}
    public double MaximumSliceMilliseconds {get;private set;}
    public double LastMilliseconds {get;private set;}

    public DoorCornerRefiner(NNModel model,WorkerFactory.Type type=WorkerFactory.Type.CSharpBurst)
    {worker=WorkerFactory.CreateWorker(type,ModelLoader.Load(model));}
    public static DoorCornerRefiner Create()
    {
        var model=Resources.Load<NNModel>("DoorNet/door_corner");
        if(model==null)return null;
        try{return new DoorCornerRefiner(model);}
        catch(Exception e){Debug.LogWarning("[DoorCornerRefiner] unavailable: "+e.Message);return null;}
    }
    public void Dispose()
    {
        if(disposed)return;disposed=true;
        if(scheduled)worker.FlushSchedule(blocking:true);worker.Dispose();
    }
    static Vector2 Signs(int index)=>new Vector2(index==0||index==2?1:-1,index<2?-1:1);
    void Prepare(DoorCameraFrame frame,Vector2[] points)
    {
        Array.Copy(points,original,4);
        doorWidth=(Vector2.Distance(points[1],points[0])+Vector2.Distance(points[3],points[2]))*.5f;
        scale=Mathf.Clamp(doorWidth*.5f,12,160)/Size;
        levels[0]=frame.gray;widths[0]=frame.width;heights[0]=frame.height;levelCount=1;
        int wanted=Mathf.Clamp(Mathf.FloorToInt(Mathf.Log(Mathf.Max(scale,1e-6f),2)),0,5);
        while(levelCount<=wanted)
        {
            int from=levelCount-1,sw=widths[from],w=sw/2,h=heights[from]/2;
            if(w<1||h<1)break;
            if(levels[levelCount]==null||levels[levelCount].Length!=w*h)levels[levelCount]=new byte[w*h];
            byte[] source=levels[from],target=levels[levelCount];
            for(int y=0;y<h;y++)for(int x=0;x<w;x++)
            {int i=2*y*sw+2*x;target[y*w+x]=(byte)((source[i]+source[i+1]+source[i+sw]+source[i+sw+1]+2)>>2);}
            widths[levelCount]=w;heights[levelCount]=h;levelCount++;
        }
        int level=levelCount-1,width=widths[level],height=heights[level];float f=1f/(1<<level);
        byte[] gray=levels[level];
        for(int corner=0;corner<4;corner++)
        {
            var sign=Signs(corner);
            for(int y=0;y<Size;y++)for(int x=0;x<Size;x++)
            {
                float sx=Mathf.Clamp((original[corner].x+(x+.5f-Size*.5f)*scale*sign.x)*f-.5f,0,width-1);
                float sy=Mathf.Clamp((original[corner].y+(y+.5f-Size*.5f)*scale*sign.y)*f-.5f,0,height-1);
                int xa=(int)sx,ya=(int)sy,xb=Math.Min(xa+1,width-1),yb=Math.Min(ya+1,height-1);
                float tx=sx-xa,ty=sy-ya;
                float top=Mathf.Lerp(gray[ya*width+xa],gray[ya*width+xb],tx);
                float bottom=Mathf.Lerp(gray[yb*width+xa],gray[yb*width+xb],tx);
                input[(corner*Size+y)*Size+x]=Mathf.Lerp(top,bottom,ty)/255f;
            }
        }
    }
    bool Decode(float[] maps,DoorCameraFrame frame,Vector2[] result,float[] scores)
    {
        bool accepted=true;float maximumMove=Mathf.Max(1.5f,doorWidth*.08f);
        for(int corner=0;corner<4;corner++)
        {
            int start=corner*Size*Size*3,best=start;
            for(int i=start+3;i<start+Size*Size*3;i+=3)if(maps[i]>maps[best])best=i;
            int cell=(best-start)/3,y=cell/Size,x=cell%Size;var sign=Signs(corner);
            scores[corner]=maps[best];
            candidate[corner]=original[corner]+Vector2.Scale(new Vector2(x+.5f+maps[best+1]-Size*.5f,y+.5f+maps[best+2]-Size*.5f),sign)*scale;
            var p=candidate[corner];
            accepted &= !float.IsNaN(scores[corner])&&!float.IsInfinity(scores[corner])&&scores[corner]>=MinimumConfidence
                &&!float.IsNaN(p.x+p.y)&&!float.IsInfinity(p.x+p.y)
                &&p.x>=0&&p.y>=0&&p.x<frame.width&&p.y<frame.height
                &&Vector2.Distance(original[corner],p)<=maximumMove;
        }
        int[] ring={0,1,3,2};float previous=0;
        for(int i=0;i<4;i++)
        {
            Vector2 a=candidate[ring[(i+1)%4]]-candidate[ring[i]],b=candidate[ring[(i+2)%4]]-candidate[ring[(i+1)%4]];
            float cross=a.x*b.y-a.y*b.x;
            accepted &= Mathf.Abs(cross)>1e-3f&&(previous==0||previous*cross>0);previous=cross;
        }
        Array.Copy(accepted?candidate:original,result,4);return accepted;
    }
    public bool TryRefine(DoorCameraFrame frame,Vector2[] points,Vector2[] result,float[] scores)
    {
        if(disposed||IsRunning)throw new InvalidOperationException("Refiner unavailable or busy");
        Prepare(frame,points);var watch=System.Diagnostics.Stopwatch.StartNew();
        using(var tensor=new Tensor(4,Size,Size,1,input))
        {worker.Execute(tensor);scheduled=true;bool accepted=Decode(worker.PeekOutput().ToReadOnlyArray(),frame,result,scores);LastMilliseconds=watch.Elapsed.TotalMilliseconds;return accepted;}
    }
    void Record(System.Diagnostics.Stopwatch watch)=>MaximumSliceMilliseconds=Math.Max(MaximumSliceMilliseconds,watch.Elapsed.TotalMilliseconds);
    public IEnumerator RefineAsync(DoorCameraFrame frame,Vector2[] points,Vector2[] result,float[] scores,Action<bool> completed,Func<bool> valid)
    {
        if(disposed||IsRunning)throw new InvalidOperationException("Refiner unavailable or busy");
        IsRunning=true;MaximumSliceMilliseconds=0;var total=System.Diagnostics.Stopwatch.StartNew();
        bool Current()=>!disposed&&(valid==null||valid());
        try
        {
            Array.Copy(points,result,4);
            var prepare=Task.Run(()=>Prepare(frame,points));
            while(!prepare.IsCompleted)yield return null;
            if(prepare.IsFaulted)throw prepare.Exception;
            if(!Current()){completed(false);yield break;}
            var slice=System.Diagnostics.Stopwatch.StartNew();
            using(var tensor=new Tensor(4,Size,Size,1,input))
            {
                Record(slice);var schedule=worker.StartManualSchedule(tensor);bool more=true;
                while(more)
                {
                    slice.Restart();do{more=schedule.MoveNext();scheduled=true;}while(more&&slice.Elapsed.TotalMilliseconds<1.5);
                    Unity.Jobs.JobHandle.ScheduleBatchedJobs();Record(slice);
                    if(more)yield return null;
                    if(!Current()){if(!disposed)worker.FlushSchedule(blocking:true);completed(false);yield break;}
                }
                var output=worker.PeekOutput();
                while(!output.PrepareCacheForAccess(blocking:false))
                {yield return null;if(!Current()){if(!disposed)worker.FlushSchedule(blocking:true);completed(false);yield break;}}
                slice.Restart();bool accepted=Decode(output.ToReadOnlyArray(),frame,result,scores);Record(slice);completed(accepted);
            }
        }
        finally{IsRunning=false;LastMilliseconds=total.Elapsed.TotalMilliseconds;}
    }
}
