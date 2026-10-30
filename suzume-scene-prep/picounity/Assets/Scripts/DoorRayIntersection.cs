using System;
using UnityEngine;

// Closest points on two forward rays. Separation/angle/gap are not acceptance gates.
public static class DoorRayIntersection
{
    public const float MaximumDistance=8f; // Initial laser display length only; never a solver limit.
    public struct Solution
    {
        public Vector3 point,firstPoint,secondPoint;
        public float firstDistance,secondDistance,gap,angle;
        public bool parallel;
    }
    public static bool TrySolve(Ray first,Ray second,out Solution solution,out string error,float preferredDepth=2f)
    {
        solution=default;error="ray_range";
        if(!Finite(first.origin)||!Finite(second.origin)||!Finite(first.direction)||!Finite(second.direction)
            || first.direction.sqrMagnitude<.001f || second.direction.sqrMagnitude<.001f) return false;
        Vector3 a=first.direction.normalized,b=second.direction.normalized,w=first.origin-second.origin;
        // Double precision and cross products avoid cancellation near parallel directions.
        double aa=Dot(a,a),bb=Dot(b,b),ab=Dot(a,b),d=Dot(a,w),e=Dot(b,w);
        double cx=(double)a.y*b.z-(double)a.z*b.y,cy=(double)a.z*b.x-(double)a.x*b.z,cz=(double)a.x*b.y-(double)a.y*b.x;
        double denominator=cx*cx+cy*cy+cz*cz;
        bool parallel=denominator<=1e-14*aa*bb;
        double s,t;
        if(parallel)
        {
            // Many equally nearest pairs: retain the previous depth (initially 2m)
            // when it belongs to that set, rather than making the preview disappear.
            s=Math.Max(0,preferredDepth);
            if(ab>0) s=Math.Max(s,-e/ab);
            else s=Math.Min(s,Math.Max(0,-e/ab));
            t=Math.Max(0,(e+ab*s)/bb);
            if(ab<0&&e<0) s=0;
        }
        else
        {
            s=(ab*e-bb*d)/denominator;
            t=(aa*e-ab*d)/denominator;
            if(s<0 || t<0)
            {
                // Infinite-line minima may be behind the hands. Compare both forward
                // ray boundaries instead, without rejecting the observation.
                double edgeT=Math.Max(0,e/bb),edgeS=Math.Max(0,-d/aa);
                if(DistanceSquared(w,a,b,0,edgeT)<=DistanceSquared(w,a,b,edgeS,0)) { s=0;t=edgeT; }
                else { s=edgeS;t=0; }
            }
        }
        Vector3 p=first.origin+a*(float)s,q=second.origin+b*(float)t;
        if(!Finite(p)||!Finite(q)) return false;
        solution=new Solution { point=(p+q)*.5f,firstPoint=p,secondPoint=q,firstDistance=(float)s,secondDistance=(float)t,
            gap=Vector3.Distance(p,q),angle=(float)(Math.Acos(Math.Min(1,Math.Abs(ab)/Math.Sqrt(aa*bb)))*180/Math.PI),parallel=parallel };
        error=null;return true;
    }
    static double Dot(Vector3 a,Vector3 b) => (double)a.x*b.x+(double)a.y*b.y+(double)a.z*b.z;
    static double DistanceSquared(Vector3 w,Vector3 a,Vector3 b,double s,double t)
    {
        double x=w.x+s*a.x-t*b.x,y=w.y+s*a.y-t*b.y,z=w.z+s*a.z-t*b.z;
        return x*x+y*y+z*z;
    }
    static bool Finite(Vector3 p) => !(float.IsNaN(p.x)||float.IsInfinity(p.x)||float.IsNaN(p.y)||float.IsInfinity(p.y)||float.IsNaN(p.z)||float.IsInfinity(p.z));
}
