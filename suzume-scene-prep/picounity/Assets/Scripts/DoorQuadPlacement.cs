using UnityEngine;

// Ordered BL, BR, TL, TR as seen from the front. Retains all four independent 3-D positions.
public static class DoorQuadPlacement
{
    public static Vector3[] Rectangle(Vector3 bottom, Quaternion rotation, float width, float height)
    {
        Vector3 side=rotation*Vector3.right*width*.5f, rise=rotation*Vector3.up*height;
        return new[]{bottom+side,bottom-side,bottom+side+rise,bottom-side+rise};
    }
    public static bool TryFit(Vector3[] points,out DoorCalibrationMath.Placement fit)
    {
        fit=default;
        if(points==null||points.Length!=4)return false;
        foreach(var p in points)if(float.IsNaN(p.x+p.y+p.z)||float.IsInfinity(p.x+p.y+p.z))return false;
        Vector3 x=(points[0]-points[1]+points[2]-points[3])*.5f;
        Vector3 y=(points[2]-points[0]+points[3]-points[1])*.5f;
        float width=x.magnitude,height=y.magnitude;
        if(width<.008f||height<.015f||width>3f||height>3.5f)return false;
        Vector3 n=Vector3.Cross(x,y);
        if(n.magnitude<width*height*.15f)return false;
        n.Normalize();Vector3 up=Vector3.Cross(n,x.normalized);
        int[] ring={0,1,3,2};float sign=0;
        for(int i=0;i<4;i++)
        {
            Vector3 a=points[ring[(i+1)%4]]-points[ring[i]],b=points[ring[(i+2)%4]]-points[ring[(i+1)%4]];
            float turn=Vector3.Dot(Vector3.Cross(a,b),n);
            if(a.magnitude<.003f||Mathf.Abs(turn)<width*height*.015f||(sign!=0&&turn*sign<0))return false;
            sign=turn;
        }
        fit=new DoorCalibrationMath.Placement { center=(points[0]+points[1])*.5f,
            rotation=Quaternion.LookRotation(n,up),width=width,height=height };
        return true;
    }
    public static Vector3[] ToLocal(Vector3[] points,Vector3 origin,Quaternion rotation)
    {
        if(points==null)return null;var result=new Vector3[points.Length];var inverse=Quaternion.Inverse(rotation);
        for(int i=0;i<points.Length;i++)result[i]=inverse*(points[i]-origin);return result;
    }
    public static Vector3[] ToWorld(Vector3[] points,Vector3 origin,Quaternion rotation)
    {
        if(points==null)return null;var result=new Vector3[points.Length];
        for(int i=0;i<points.Length;i++)result[i]=origin+rotation*points[i];return result;
    }
    public static bool HasFourFiniteCorners(Vector3[] corners)
    {
        if(corners==null || corners.Length!=4)return false;
        foreach(var c in corners)
            if(float.IsNaN(c.x)||float.IsNaN(c.y)||float.IsNaN(c.z)||
               float.IsInfinity(c.x)||float.IsInfinity(c.y)||float.IsInfinity(c.z))return false;
        // Four zero vectors are also an unset serialized value, not a door opening.
        Vector3 across=(corners[0]-corners[1]+corners[2]-corners[3])*.5f;
        Vector3 up=(corners[2]-corners[0]+corners[3]-corners[1])*.5f;
        return Vector3.Cross(across,up).sqrMagnitude>1e-16f;
    }
    public static Vector3 Warp(Vector3 p,Vector3[] corners)
    {
        if(!HasFourFiniteCorners(corners))return p;
        float u=.5f-p.x/PortalConfig.BaseDoorWidth, v=p.y/PortalConfig.BaseDoorHeight;
        Vector3 bottom=Vector3.LerpUnclamped(corners[0],corners[1],u);
        Vector3 top=Vector3.LerpUnclamped(corners[2],corners[3],u);
        return Vector3.LerpUnclamped(bottom,top,v)+Vector3.forward*p.z;
    }
}
