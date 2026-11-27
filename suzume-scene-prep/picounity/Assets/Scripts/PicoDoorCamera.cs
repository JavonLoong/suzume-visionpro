using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Unity.XR.PXR;
using UnityEngine;

public sealed class DoorCameraFrame
{
    public byte[] gray; // one byte per pixel, row 0 at the top
    public int width, height;
    public float fx, fy, cx, cy, time;
    public Matrix4x4 cameraToWorld;
    public bool poseCorrected; public float captureAge;
}

// Unity's world pose and the native reference pose must belong to the same sampled frame.
// Keep this value immutable while camera copying/inference waits on background work.
public struct DoorCameraPoseSample
{
    public Matrix4x4 headToWorld;
    public float time;
    public double displayTimeMilliseconds;
    public Pose nativeHead;
    public bool nativeValid;
}

// Finds the four inner corners of the door opening in a camera frame.
// Order: bottom-left, bottom-right, top-left, top-right; pixels with a top-left origin.
public interface IDoorKeypointDetector
{
    bool TryDetect(DoorCameraFrame frame, Vector2[] pixels, float[] confidence);
}

public interface IDoorGuidedDetector
{
    bool TryDetectGuided(DoorCameraFrame frame, Rect searchRegion, Vector2[] pixels, float[] confidence);
    void Reset();
}

// PICO 4 Ultra colour camera through PXR_CameraImage (system 5.15.0 or later, android.permission.CAMERA).
public sealed class PicoDoorCamera : IDisposable
{
    const string Permission = "android.permission.CAMERA";
    readonly XrCameraIdPICO _id;
    readonly CancellationTokenSource _lifetime = new CancellationTokenSource();
    bool _device, _session, _capturing;
    long _lastCapture;
    byte[] _rgba;
    Matrix4x4 _headToCamera = Matrix4x4.identity;
    float _fx, _fy, _cx, _cy;
    EnterpriseDoorCamera _enterprise;

    public bool IsRunning => _enterprise != null ? _enterprise.IsRunning : _capturing;
    public int Width { get; private set; }
    public int Height { get; private set; }
    public string Failure { get; private set; }

    public PicoDoorCamera(XrCameraIdPICO id = XrCameraIdPICO.XR_CAMERA_ID_RGB_LEFT_PICO) { _id = id; }

    public static bool HasPermission => UnityEngine.Android.Permission.HasUserAuthorizedPermission(Permission);
    public static void RequestPermission() => UnityEngine.Android.Permission.RequestUserPermission(Permission);

    public async Task<bool> StartAsync(int preferredWidth = 2048)
    {
        try
        {
            var available = PXR_CameraImage.GetAvailableCameras(out var cameras);
            if (available != PxrResult.SUCCESS || cameras == null || Array.IndexOf(cameras, _id) < 0)
            {
                Debug.LogWarning("[DoorCamera] OpenXR enumeration=" + available + "; checking enterprise camera compatibility");
                if (!EnterpriseDoorCamera.IsSupportedDevice()) return Fail("camera API unavailable on this device/system");
                _enterprise = new EnterpriseDoorCamera();
                if (!await _enterprise.StartAsync(_lifetime.Token)) return Fail(_enterprise.Failure);
                Width = _enterprise.Width; Height = _enterprise.Height;
                return true;
            }
            if (PXR_CameraImage.GetCameraImageResolutionCapability(_id, out var resolutions) != PxrResult.SUCCESS || resolutions.Length == 0)
                return Fail("no resolution list");
            // The door is only a few centimetres tall, so take the resolution closest to the preferred width.
            var chosen = resolutions[0];
            foreach (var r in resolutions)
                if (Math.Abs(r.width - preferredWidth) < Math.Abs(chosen.width - preferredWidth)) chosen = r;
            var result = await PXR_CameraImage.CreateCameraDeviceAsync(_id, _lifetime.Token);
            if (result != PxrResult.SUCCESS) return Fail("create device " + result);
            _device = true;
            result = await PXR_CameraImage.CreateCameraCaptureSessionAsync(_id, chosen.width, chosen.height,
                XrCameraImageFpsPICO.XR_CAMERA_IMAGE_FPS_30_PICO, XrCameraImageFormatPICO.XR_CAMERA_IMAGE_FORMAT_RGBA_8888_PICO,
                XrCameraDataTransferTypePICO.XR_CAMERA_DATA_TRANSFER_TYPE_RAW_BUFFER_PICO, XrCameraModelPICO.XR_CAMERA_MODEL_PINHOLE_PICO, _lifetime.Token);
            if (result != PxrResult.SUCCESS) return Fail("create session " + result);
            _session = true;
            if (PXR_CameraImage.GetCameraIntrinsics(_id, out var intrinsics) != PxrResult.SUCCESS) return Fail("intrinsics");
            if (PXR_CameraImage.GetCameraExtrinsics(_id, out var extrinsics) != PxrResult.SUCCESS) return Fail("extrinsics");
            _fx = intrinsics.focalLength.X; _fy = intrinsics.focalLength.Y; _cx = intrinsics.principalPoint.X; _cy = intrinsics.principalPoint.Y;
            var pose = extrinsics.pose;
            _headToCamera = Matrix4x4.TRS(new Vector3(pose.Position.X, pose.Position.Y, pose.Position.Z),
                new Quaternion(pose.Orientation.X, pose.Orientation.Y, pose.Orientation.Z, pose.Orientation.W), Vector3.one);
            result = PXR_CameraImage.BeginCameraCapture(_id);
            if (result != PxrResult.SUCCESS) return Fail("begin capture " + result);
            Width = chosen.width; Height = chosen.height; _capturing = true;
            Debug.Log($"[DoorCamera] {_id} {Width}x{Height} f=({_fx:F1},{_fy:F1}) c=({_cx:F1},{_cy:F1}) fov=({intrinsics.fov.X:F1},{intrinsics.fov.Y:F1}) offset={_headToCamera.GetColumn(3)}");
            return true;
        }
        catch (Exception e) { return Fail(e.Message); }
    }

    // Call on the main thread in the same frame as sampling Camera.main, BEFORE Task.Run.
    public DoorCameraPoseSample SamplePose(Matrix4x4 headToWorld, float time) =>
        _enterprise != null ? _enterprise.SamplePose(headToWorld, time)
            : new DoorCameraPoseSample { headToWorld = headToWorld, time = time };

    // The snapshot is already paired; the copy and grey conversion may run on a worker.
    public bool TryAcquire(DoorCameraPoseSample sample, DoorCameraFrame frame)
    {
        if (_enterprise != null) return _enterprise.TryAcquire(sample, frame);
        if (!_capturing) return false;
        if (PXR_CameraImage.AcquireCameraImage(_id, _lastCapture, out ulong image, out long captured) != PxrResult.SUCCESS) return false;
        try
        {
            if (PXR_CameraImage.GetCameraImageData(_id, image, out var data) != PxrResult.SUCCESS || data.buffer == IntPtr.Zero) return false;
            int width = (int)data.width, height = (int)data.height, stride = (int)data.stride, step = (int)data.pixelStride;
            if (width <= 0 || height <= 0 || step < 3 || stride < width * step || data.bufferSize < (uint)(stride * (height - 1) + width * step)) return false;
            if (_rgba == null || _rgba.Length < data.bufferSize) _rgba = new byte[data.bufferSize];
            Marshal.Copy(data.buffer, _rgba, 0, (int)data.bufferSize);
            if (frame.gray == null || frame.gray.Length != width * height) frame.gray = new byte[width * height];
            for (int y = 0; y < height; y++)
            {
                int source = y * stride, target = y * width;
                for (int x = 0; x < width; x++, source += step)
                    frame.gray[target + x] = (byte)((_rgba[source] * 77 + _rgba[source + 1] * 150 + _rgba[source + 2] * 29) >> 8);
            }
            // Intrinsics are reported for the session size; rescale if the buffer differs.
            float sx = width / (float)Width, sy = height / (float)Height;
            frame.width = width; frame.height = height; frame.time = sample.time;
            frame.fx = _fx * sx; frame.fy = _fy * sy; frame.cx = _cx * sx; frame.cy = _cy * sy;
            frame.cameraToWorld = sample.headToWorld * _headToCamera;
            frame.poseCorrected = false; frame.captureAge = float.NaN;
            _lastCapture = captured;
            return true;
        }
        finally { PXR_CameraImage.ReleaseCameraImage(_id, image); }
    }

    bool Fail(string reason)
    {
        Failure = reason;
        Debug.LogWarning("[DoorCamera] unavailable: " + reason);
        Release();
        return false;
    }
    void Release()
    {
        _enterprise?.Dispose();
        if (_capturing) PXR_CameraImage.EndCameraCapture(_id);
        if (_session) PXR_CameraImage.DestroyCameraCaptureSession(_id);
        if (_device) PXR_CameraImage.DestroyCameraDevice(_id);
        _capturing = _session = _device = false;
    }
    public void Dispose() { _lifetime.Cancel(); Release(); }
}
