using System;
using System.IO;
using UnityEngine;

public static class PortalRayTrialCheck
{
    static void Require(bool condition,string message) { if(!condition)throw new Exception(message); }
    static Ray Aim(Vector3 origin,Vector3 target) => new Ray(origin,(target-origin).normalized);
    public static void Run()
    {
        Vector3 target=new Vector3(0,1,0),a=new Vector3(-.3f,1,2),b=new Vector3(.3f,1,2);
        Require(DoorRayIntersection.TrySolve(Aim(a,target),Aim(b,target),out var hit,out _),"two observations of the same target failed");
        Require(Vector3.Distance(hit.point,target)<.001f&&hit.gap<.001f,"rays did not recover the distant target");
        Require(DoorRayIntersection.TrySolve(Aim(a,target),Aim(a,target+Vector3.right),out hit,out _)&&hit.gap<.001f,"same-origin preview disappeared");
        Require(DoorRayIntersection.TrySolve(Aim(a,target),Aim(a+Vector3.right*.02f,target),out hit,out _)&&Vector3.Distance(hit.point,target)<.001f,"2cm baseline preview disappeared");
        Require(DoorRayIntersection.TrySolve(new Ray(a,Vector3.back),new Ray(b,Vector3.back),out hit,out _,3f)&&hit.parallel&&Mathf.Abs(hit.firstDistance-3)<.001f&&Mathf.Abs(hit.gap-.6f)<.001f,"parallel closest-pair preview lost previous depth or distance");
        var distant=new Vector3(0,1,-20);
        Require(DoorRayIntersection.TrySolve(Aim(a,distant),Aim(b,distant),out hit,out _)&&Vector3.Distance(hit.point,distant)<.002f,"nearly parallel / distant closest point disappeared");
        Require(DoorRayIntersection.TrySolve(Aim(a,target),Aim(b+Vector3.up*.2f,target+Vector3.up*.2f),out hit,out _),"closest-point preview disappeared when the rays miss by 20cm");
        Require(Mathf.Abs(hit.gap-.2f)<.001f&&Vector3.Distance(hit.point,target+Vector3.up*.1f)<.001f,"skew-ray midpoint incorrect");
        Require(Vector3.Distance(hit.firstPoint,target)<.001f&&Vector3.Distance(hit.secondPoint,target+Vector3.up*.2f)<.001f,"nearest endpoint markers incorrect");
        Vector3 bridge=hit.secondPoint-hit.firstPoint;
        Require(Mathf.Abs(Vector3.Dot(bridge,Aim(a,target).direction))<.001f&&Mathf.Abs(Vector3.Dot(bridge,Aim(b+Vector3.up*.2f,target+Vector3.up*.2f).direction))<.001f,"closest bridge is not perpendicular to both rays");
        Require(DoorRayIntersection.TrySolve(Aim(a,target),Aim(b+Vector3.up*.03f,target+Vector3.up*.03f),out hit,out _),"small aiming error was not tolerated");
        Require(Vector3.Distance(hit.point,target+Vector3.up*.015f)<.001f&&Mathf.Abs(hit.gap-.03f)<.001f,"closest-approach midpoint is incorrect");
        Require(DoorRayIntersection.TrySolve(new Ray(a,(a-target).normalized),new Ray(b,(b-target).normalized),out hit,out _)&&hit.firstDistance==0&&hit.secondDistance==0,"diverging rays did not retain closest forward endpoints");
        Require(DoorRayIntersection.TrySolve(Aim(new Vector3(-2,1,2),distant),Aim(new Vector3(2,1,2),distant),out hit,out _)&&Vector3.Distance(hit.point,distant)<.002f,"8m cutoff still present");
        Require(!DoorRayIntersection.TrySolve(new Ray(new Vector3(float.NaN,0,0),Vector3.forward),Aim(b,target),out _,out _),"invalid input accepted");
        for(int i=-1000;i<=1000;i++)
        {
            var first=new Ray(a,Vector3.back);
            var second=new Ray(b+Vector3.up*.2f,Quaternion.Euler(0,i*.02f,0)*Vector3.back);
            Require(DoorRayIntersection.TrySolve(first,second,out hit,out _),"sweep preview disappeared at "+i);
            Require(hit.firstDistance>=0&&hit.secondDistance>=0&&!float.IsNaN(hit.gap),"sweep produced invalid forward points");
            Vector3 delta=hit.firstPoint-hit.secondPoint;
            float firstGradient=Vector3.Dot(delta,first.direction),secondGradient=-Vector3.Dot(delta,second.direction);
            Require(hit.firstDistance>.0001f ? Mathf.Abs(firstGradient)<.002f : firstGradient>=-.002f,"not closest on first ray at "+i);
            Require(hit.secondDistance>.0001f ? Mathf.Abs(secondGradient)<.002f : secondGradient>=-.002f,"not closest on second ray at "+i);
        }
        foreach(float baseline in new[]{0f,.02f,.149f,.15f,.151f,.6f})
            Require(DoorRayIntersection.TrySolve(Aim(a,target),Aim(a+Vector3.right*baseline,target),out _,out _),"old baseline cutoff at "+baseline);
        // Opposite parallel rays: overlapping forward intervals and separated intervals.
        Require(DoorRayIntersection.TrySolve(new Ray(Vector3.zero,Vector3.right),new Ray(new Vector3(4,1,0),Vector3.left),out hit,out _,3f)&&Mathf.Abs(hit.gap-1)<.001f&&Mathf.Abs(hit.firstDistance-3)<.001f,"opposite parallel overlap wrong");
        Require(DoorRayIntersection.TrySolve(new Ray(Vector3.zero,Vector3.right),new Ray(new Vector3(-4,1,0),Vector3.left),out hit,out _)&&hit.firstDistance==0&&hit.secondDistance==0,"opposite separated ray endpoints wrong");
        // Eight observations recover the four corners after an arbitrary tracking-origin transform.
        var corners=new[]{new Vector3(.5f,0,0),new Vector3(-.5f,0,0),new Vector3(.5f,2.1f,0),new Vector3(-.5f,2.1f,0)};
        var rotation=Quaternion.Euler(0,37,0);var offset=new Vector3(3,.4f,-2);var selected=new Vector3[4];
        for(int i=0;i<4;i++)
        {
            var first=Aim(a,corners[i]);var second=Aim(b,corners[i]);
            first=new Ray(offset+rotation*first.origin,rotation*first.direction);
            second=new Ray(offset+rotation*second.origin,rotation*second.direction);
            Require(DoorRayIntersection.TrySolve(first,second,out hit,out _),"paired rays failed for corner "+i);
            selected[i]=hit.point;
        }
        Require(DoorCalibrationMath.TryFit(selected,offset+rotation*new Vector3(0,1.6f,2),out var fit,out _),"four paired-ray corners did not form a valid door");
        Require(Mathf.Abs(fit.width-1f)<.001f&&Mathf.Abs(fit.height-2.1f)<.001f,"paired-ray door dimensions wrong");
        ControllerTrialCheck.Run();
        Directory.CreateDirectory("Builds/controller-check");
        File.WriteAllText("Builds/controller-check/ray-result.txt","PASS: closest forward-ray endpoints and midpoint; 20cm gap accepted; 2001-direction sweep through 0/5-degree boundaries with optimality checks; zero/2cm/15cm baselines retained; parallel depth retained; diverging/antiparallel cases; no 8m cutoff; invalid input rejected; eight transformed observations recover four corners; controller/scene/UI checks passed.\n");
        Debug.Log("[PortalRayTrialCheck] ALL TWO-RAY CHECKS PASSED");
    }
}
