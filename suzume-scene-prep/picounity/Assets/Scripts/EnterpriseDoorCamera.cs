using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Unity.XR.PICO.TOBSupport;
using UnityEngine;

// PICO 4 Ultra Enterprise's documented capture API, for systems without XR_PICO_camera_image.
public sealed class EnterpriseDoorCamera : IDisposable
{
    public int Width => 2048;
    public int Height => 1536;
    public bool IsRunning { get; private set; }
    public string Failure { get; private set; }
    readonly object gate = new object();
    IntPtr buffer;
    byte[] latest;
    ulong timestamp, consumed;
    long receivedTicks;
    bool accepting, opened, disposed, saved, poseLogged, poseFallbackLogged;
    float fx, fy, cx, cy;
    Matrix4x4 headToCamera;
    string diagnosticPath;

    public static bool IsSupportedDevice()
    {
        if (Application.platform != RuntimePlatform.Android) return false;
        using (var props = new AndroidJavaClass("android.os.SystemProperties"))
        {
            string model = props.CallStatic<string>("get", "pxr.vendorhw.product.model", "");
            string system = props.CallStatic<string>("get", "ro.pui.build.version", "");
            Debug.Log("[DoorCamera] device=" + model + " system=" + system);
            return model.IndexOf("PICO 4 Ultra Enterprise", StringComparison.OrdinalIgnoreCase) >= 0;
        }
    }

    public async Task<bool> StartAsync(CancellationToken cancellation)
    {
        try
        {
            diagnosticPath = Path.Combine(Application.persistentDataPath, "doorcam_enterprise_first.pgm");
            if (!await AwaitResult(PicoEnterpriseConnection.EnsureAsync(), cancellation)) return Fail("enterprise service binding failed/timed out");
            Debug.Log("[DoorCamera] using shared enterprise service connection");
            PXR_Enterprise.Configurefor4U(new Dictionary<string, string> {
                { PXRCapture.KEY_OUTPUT_CAMERA_RAW_DATA, PXRCapture.VALUE_FALSE }
            });
            var ready = new TaskCompletionSource<bool>();
            PXR_Enterprise.OpenCameraAsyncfor4U(ok => ready.TrySetResult(ok), new Dictionary<string,string> {
                { PXRCapture.KEY_EIS, PXRCapture.VALUE_FALSE },
                { PXRCapture.KEY_MCTF, PXRCapture.VALUE_FALSE }
            });
            opened = true; // Also close a partially opened session after timeout.
            if (!await AwaitResult(ready.Task, cancellation)) return Fail("enterprise camera opening failed/timed out");
            cancellation.ThrowIfCancellationRequested();
            var p = PXR_Enterprise.GetCameraParametersNewfor4U(Width, Height);
            if (!ValidIntrinsics(p.fx, p.fy, p.cx, p.cy, Width, Height)) return Fail("enterprise camera calibration unavailable");
            fx=(float)p.fx; fy=(float)p.fy; cx=(float)p.cx; cy=(float)p.cy;
            headToCamera=CalibrationToUnity(p.l_pos,p.l_rot);
            if (Quaternion.Dot(p.l_rot,p.l_rot) < .5f || p.l_pos.magnitude > 1f) return Fail("enterprise camera extrinsics invalid");
            buffer=Marshal.AllocHGlobal(Width*Height*4);
            latest=new byte[Width*Height*4];
            accepting=true;
            PXR_Enterprise.SetCameraFrameBufferfor4U(Width, Height, ref buffer, OnFrame);
            if (!PXR_Enterprise.StartGetImageDatafor4U(PXRCaptureRenderMode.PXRCapture_RenderMode_LEFT, Width, Height))
                return Fail("enterprise image stream rejected");
            IsRunning=true;
            Debug.Log($"[DoorCamera] enterprise stream {Width}x{Height} f=({fx},{fy}) c=({cx},{cy}) position={p.l_pos:F4} rotation={p.l_rot:F4}");
            Debug.Log($"[DoorCamera] Unity optical centre={headToCamera.GetColumn(3):F4} forward={headToCamera.GetColumn(2):F4}");
            return true;
        }
        catch(Exception e) { return Fail("enterprise " + e.Message); }
    }

    static async Task<bool> AwaitResult(Task<bool> result, CancellationToken cancel)
    {
        var winner=await Task.WhenAny(result, Task.Delay(6000, cancel));
        cancel.ThrowIfCancellationRequested();
        return winner==result && await result;
    }

    public static bool ValidIntrinsics(double fx, double fy, double cx, double cy, int width, int height)
    {
        return !double.IsNaN(fx+fy+cx+cy) && !double.IsInfinity(fx+fy+cx+cy)
            && fx>0 && fy>0 && cx>=0 && cx<width && cy>=0 && cy<height;
    }

    // Calibration relates optical coordinates (X right, Y down, Z forward) to the native
    // right-handed head space (X right, Y up, Z back). Our solver uses Unity Y up/Z forward.
    // Convert BOTH bases. Applying the raw quaternion alone points the search behind the HMD.
    public static Matrix4x4 CalibrationToUnity(Vector3 position,Quaternion rotation)
    {
        return Matrix4x4.Scale(new Vector3(1,1,-1))
            * Matrix4x4.TRS(position,rotation,Vector3.one)
            * Matrix4x4.Scale(new Vector3(1,-1,1));
    }

    public static Matrix4x4 NativeHeadToUnity(UnityEngine.Pose pose)
    {
        var flip=Matrix4x4.Scale(new Vector3(1,1,-1));
        return flip*Matrix4x4.TRS(pose.position,pose.rotation,Vector3.one)*flip;
    }
    public static bool TryCapturePose(Matrix4x4 headToWorld,UnityEngine.Pose captured,UnityEngine.Pose current,out Matrix4x4 result)
    {
        result=headToWorld;
        float sum=captured.position.sqrMagnitude+current.position.sqrMagnitude;
        float capturedNorm=Quaternion.Dot(captured.rotation,captured.rotation), currentNorm=Quaternion.Dot(current.rotation,current.rotation);
        if(float.IsNaN(sum)||float.IsInfinity(sum)||float.IsNaN(capturedNorm+currentNorm)||float.IsInfinity(capturedNorm+currentNorm)
            ||capturedNorm<.5f||currentNorm<.5f||capturedNorm>1.5f||currentNorm>1.5f)return false;
        for(int i=0;i<16;i++)if(float.IsNaN(headToWorld[i])||float.IsInfinity(headToWorld[i]))return false;
        if(Vector3.Distance(captured.position,current.position)>.3f||Quaternion.Angle(captured.rotation,current.rotation)>60)return false;
        result=headToWorld*NativeHeadToUnity(current).inverse*NativeHeadToUnity(captured);
        return true;
    }

    void OnFrame(Frame native)
    {
        lock(gate)
        {
            if (!accepting || disposed || native.data==IntPtr.Zero || native.width!=Width || native.height!=Height
                || native.datasize < latest.Length || native.timestamp==0) return;
            Marshal.Copy(native.data, latest, 0, latest.Length);
            timestamp=native.timestamp;
            receivedTicks=System.Diagnostics.Stopwatch.GetTimestamp();
        }
    }

    public bool TryAcquire(Matrix4x4 headToWorld, float time, DoorCameraFrame frame)
    {
        lock(gate)
        {
            if (!IsRunning || disposed || timestamp==0 || timestamp==consumed) return false;
            double age=(System.Diagnostics.Stopwatch.GetTimestamp()-receivedTicks)/(double)System.Diagnostics.Stopwatch.Frequency;
            if(age>.25) return false;
            if(frame.gray==null || frame.gray.Length!=Width*Height) frame.gray=new byte[Width*Height];
            RgbaToGray(latest, frame.gray, Width, Height);
            frame.width=Width; frame.height=Height; frame.time=time;
            frame.fx=fx; frame.fy=fy; frame.cx=cx; frame.cy=cy;
            // Relate capture pose to the predicted display pose in the SAME native tracking
            // origin, then apply that relative motion to OpenXR's sampled world pose. This avoids
            // assuming that native tracking and the application's world origin coincide.
            // Keep the verified 1.12.8 capture path when native sensor timing is unavailable.
            // In particular, some OpenXR configurations expose the camera but not this sensor API.
            frame.cameraToWorld=headToWorld*headToCamera;frame.poseCorrected=false;frame.captureAge=(float)age;
            try
            {
                double displayTime=PXR_Enterprise.GetPredictedDisplayTime();
                double capturedTime=timestamp/1000000.0; // keep nanoseconds -> milliseconds in double precision
                double seconds=(displayTime-capturedTime)/1000.0;
                var current=PXR_Enterprise.GetPredictedMainSensorState(displayTime,false);
                var captured=PXR_Enterprise.GetPredictedMainSensorState(capturedTime,false);
                if(current.status==1&&captured.status==1&&seconds>=-.01&&seconds<=.3
                    &&TryCapturePose(headToWorld,captured.pose,current.pose,out var captureHead))
                {
                    frame.cameraToWorld=captureHead*headToCamera;frame.time=time-(float)System.Math.Max(0,seconds);
                    frame.poseCorrected=true;frame.captureAge=(float)System.Math.Max(0,seconds);
                    if(!poseLogged){poseLogged=true;Debug.Log($"[DoorCamera] capture-time pose correction active age={seconds*1000:F1}ms");}
                }
            }
            catch(Exception e){if(!poseFallbackLogged)Debug.LogWarning("[DoorCamera] native pose correction unavailable: "+e.Message);}
            if(!frame.poseCorrected&&!poseFallbackLogged)
            {poseFallbackLogged=true;Debug.LogWarning("[DoorCamera] using sampled head pose; capture stream remains available, capture-time correction is unverified");}
            consumed=timestamp;
        }
        if(!saved)
        {
            saved=true;
            try {
                using(var output=File.Create(diagnosticPath)) {
                    byte[] header=System.Text.Encoding.ASCII.GetBytes($"P5\n{Width} {Height}\n255\n");
                    output.Write(header,0,header.Length); output.Write(frame.gray,0,frame.gray.Length);
                }
                Debug.Log("[DoorCamera] enterprise first frame received; diagnostic="+diagnosticPath);
            } catch(Exception e) { Debug.LogWarning("[DoorCamera] first frame diagnostic: "+e.Message); }
        }
        return true;
    }

    public static void RgbaToGray(byte[] rgba, byte[] gray, int width, int height)
    {
        if(width<=0 || height<=0 || (long)width*height*4>rgba.Length || (long)width*height>gray.Length)
            throw new ArgumentException("Invalid RGBA frame size");
        for(int i=0, s=0;i<width*height;i++,s+=4)
            gray[i]=(byte)((rgba[s]*77+rgba[s+1]*150+rgba[s+2]*29)>>8);
    }

    bool Fail(string reason) { Failure=reason; Dispose(); return false; }
    public void Dispose()
    {
        lock(gate) { if(disposed) return; disposed=true; accepting=false; IsRunning=false; }
        // Stop the native producer before freeing its write buffer; do not hold gate while stopping.
        bool closed=!opened;
        if(opened) { try { closed=PXR_Enterprise.CloseCamerafor4U(); } catch(Exception e) { Debug.LogWarning("[DoorCamera] close enterprise: "+e.Message); } }
        if(closed && buffer!=IntPtr.Zero) { Marshal.FreeHGlobal(buffer); buffer=IntPtr.Zero; }
        if(!closed) Debug.LogWarning("[DoorCamera] native close failed; retaining capture buffer until process exit");
    }
}
