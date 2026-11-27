using System;
using System.IO;
using UnityEngine;

public static class DoorCaptureTimingCheck
{
    static void Require(bool ok,string message){if(!ok)throw new Exception(message);}
    static float MatrixError(Matrix4x4 a,Matrix4x4 b)
    {float maximum=0;for(int i=0;i<16;i++)maximum=Mathf.Max(maximum,Mathf.Abs(a[i]-b[i]));return maximum;}
    public static void Run()
    {
        var captured=new Pose(new Vector3(.10f,1.60f,-.30f),Quaternion.Euler(2,12,-1));
        var reference=new Pose(new Vector3(.12f,1.61f,-.31f),Quaternion.Euler(3,15,1));
        var origin=Matrix4x4.TRS(new Vector3(12,.8f,-3),Quaternion.Euler(0,47,0),Vector3.one);
        var sample=new DoorCameraPoseSample {headToWorld=origin*EnterpriseDoorCamera.NativeHeadToUnity(reference),
            nativeHead=reference,nativeValid=true,time=123.4f,displayTimeMilliseconds=456789.125};
        var expected=origin*EnterpriseDoorCamera.NativeHeadToUnity(captured);
        Require(EnterpriseDoorCamera.TryCaptureFramePose(sample,captured,456749.125,out var actual,out var time,out var age),"paired sample rejected");
        Require(MatrixError(actual,expected)<.00002f,"capture pose lost world/tracking origin conversion");
        Require(Mathf.Abs(time-123.36f)<.00002f&&Mathf.Abs(age-.04f)<.000001f,"capture timestamp drift");
        var later=reference;later.position+=new Vector3(.04f,0,0);later.rotation=Quaternion.Euler(3,20,1);
        Require(EnterpriseDoorCamera.TryCapturePose(sample.headToWorld,captured,later,out var oldMixed),"old delay reproduction failed");
        float oldError=Vector3.Distance(oldMixed.GetColumn(3),expected.GetColumn(3))*1000;
        Require(oldError>10,"test did not reproduce mismatched sample error");
        // Background work may start in a later frame. The same immutable snapshot must
        // produce the same capture pose, not incorporate the later native head pose.
        for(int delay=0;delay<4;delay++)
        {
            later.position+=Vector3.right*.03f;
            Require(EnterpriseDoorCamera.TryCaptureFramePose(sample,captured,456749.125,out actual,out time,out age)
                &&MatrixError(actual,expected)<.00002f,"worker delay changed capture pose");
        }
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(sample,captured,456000,out _,out _,out _),"stale native frame accepted");
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(sample,captured,456809.125,out _,out _,out _),"future native frame accepted");
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(sample,captured,double.NaN,out _,out _,out _),"NaN timestamp accepted");
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(sample,captured,double.PositiveInfinity,out _,out _,out _),"infinite timestamp accepted");
        var bad=sample;bad.nativeValid=false;
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(bad,captured,456749.125,out _,out _,out _),"missing reference marked corrected");
        bad=sample;bad.nativeHead.rotation=new Quaternion(0,0,0,0);
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(bad,captured,456749.125,out _,out _,out _),"invalid reference quaternion accepted");
        bad=sample;bad.time=float.NaN;
        Require(!EnterpriseDoorCamera.TryCaptureFramePose(bad,captured,456749.125,out _,out _,out _),"invalid app time accepted");
        string report=$"PASS: paired Unity/native pose; displaced and rotated tracking origin; delayed worker; stale/future/nonfinite timestamps; missing/invalid reference. Old mismatched-pose fixture error={oldError:F3}mm, corrected matrix error={MatrixError(actual,expected):F8}. This is deterministic PC simulation, not headset accuracy.\n";
        File.WriteAllText("D:/suzume-integration-20261127/precision-crop/capture-timing-check.txt",report);
        Debug.Log("[DoorCaptureTimingCheck] "+report);
    }
}
