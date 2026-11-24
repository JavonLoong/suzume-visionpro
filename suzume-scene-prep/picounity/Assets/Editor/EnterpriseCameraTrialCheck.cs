using System;
using UnityEngine;

public static class EnterpriseCameraTrialCheck
{
    public static void Run()
    {
        var flags=System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic;
        var connected=typeof(PicoEnterpriseConnection).GetField("connected",flags);
        var pending=typeof(PicoEnterpriseConnection).GetField("pending",flags);
        object oldConnected=connected.GetValue(null), oldPending=pending.GetValue(null);
        try {
            var waiting=new System.Threading.Tasks.TaskCompletionSource<bool>();
            connected.SetValue(null,false); pending.SetValue(null,waiting.Task);
            if(!ReferenceEquals(PicoEnterpriseConnection.EnsureAsync(),waiting.Task)
                || !ReferenceEquals(PicoEnterpriseConnection.EnsureAsync(),waiting.Task))
                throw new Exception("Concurrent consumers did not share the pending bind");
            connected.SetValue(null,true); waiting.SetResult(true);
            if(!PicoEnterpriseConnection.EnsureAsync().Result)
                throw new Exception("Already connected service was not reused");
        } finally { connected.SetValue(null,oldConnected); pending.SetValue(null,oldPending); }
        // Factory calibration captured from this headset: a front camera must project a
        // point in front of the user's head into the image, not reject it as behind-camera.
        var optical=EnterpriseDoorCamera.CalibrationToUnity(new Vector3(-.0325f,-.0021f,-.0685f),
            new Quaternion(1,.0016f,-.0034f,.0016f).normalized);
        var target=new Vector3(0,0,.6f);
        var local=optical.inverse.MultiplyPoint3x4(target);
        if(local.z<.5f || Vector3.Dot(optical.MultiplyVector(Vector3.forward),Vector3.forward)<.99f
            || optical.GetColumn(3).z<.05f || Mathf.Abs(optical.determinant-1)>1e-4)
            throw new Exception("Measured front-camera calibration points in the wrong direction");
        var cameraFrame=new DoorCameraFrame {width=2048,height=1536,fx=1302.441f,fy=1302.505f,cx=1023.5f,cy=767.5f,cameraToWorld=optical};
        var hint=new DoorSearchHint(); hint.Set(new Ray(new Vector3(.2f,-.15f,.1f),target-new Vector3(.2f,-.15f,.1f)));
        hint.Focus(target);
        if(!hint.TryCrop(cameraFrame,.0558f,out var crop) || !crop.Contains(new Vector2(cameraFrame.cx+cameraFrame.fx*local.x/local.z,cameraFrame.cy-cameraFrame.fy*local.y/local.z)))
            throw new Exception("Forward controller target is outside the measured-camera search");
        byte[] input={255,0,0,255, 0,255,0,255, 0,0,255,255, 255,255,255,255};
        byte[] output=new byte[4];
        EnterpriseDoorCamera.RgbaToGray(input,output,2,2);
        if(output[0]!=76 || output[1]!=149 || output[2]!=28 || output[3]!=255)
            throw new Exception("RGBA row/channel conversion failed");
        bool rejected=false;
        try { EnterpriseDoorCamera.RgbaToGray(new byte[3],new byte[1],1,1); }
        catch(ArgumentException) { rejected=true; }
        if(!rejected) throw new Exception("Truncated buffer accepted");
        if(EnterpriseDoorCamera.ValidIntrinsics(0,0,0,0,2048,1536)
            || EnterpriseDoorCamera.ValidIntrinsics(double.NaN,1000,1024,768,2048,1536)
            || !EnterpriseDoorCamera.ValidIntrinsics(1400,1400,1024,768,2048,1536))
            throw new Exception("Calibration validity gate failed");
        GuidedDoorTrialCheck.Run();
        Debug.Log("[EnterpriseCameraTrialCheck] PASS; hardware stream still requires device verification");
    }
}
