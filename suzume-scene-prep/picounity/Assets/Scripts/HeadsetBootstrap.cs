using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.XR;

/// <summary>
/// 头显启动：把主相机放到门外，并交给 OpenXR 头部位姿。
/// 桌面 Play 模式不改相机，避免影响已有预览。
/// </summary>
public static class HeadsetBootstrap
{
    public static Transform Origin { get; private set; }

    const float StandDistance = 2.4f;
    const float FallbackEyeHeight = 1.6f;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void AfterSceneLoad()
    {
        if (Application.isEditor || Application.platform != RuntimePlatform.Android)
            return;

        var cam = Camera.main;
        if (cam == null)
            return;

        var origin = new GameObject("HeadsetOrigin");
        Origin = origin.transform;
        origin.transform.SetPositionAndRotation(
            new Vector3(0f, 0f, StandDistance),
            Quaternion.Euler(0f, 180f, 0f));

        cam.transform.SetParent(origin.transform, false);
        cam.transform.localPosition = new Vector3(0f, FallbackEyeHeight, 0f);
        cam.transform.localRotation = Quaternion.identity;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = Color.clear;
        cam.nearClipPlane = 0.05f;

        var driver = cam.gameObject.GetComponent<TrackedPoseDriver>();
        if (driver == null)
            driver = cam.gameObject.AddComponent<TrackedPoseDriver>();

        driver.enabled = false;
        driver.trackingType = TrackedPoseDriver.TrackingType.RotationAndPosition;
        driver.positionInput = new InputActionProperty(
            new InputAction("HMD Position", binding: "<XRHMD>/centerEyePosition"));
        driver.rotationInput = new InputActionProperty(
            new InputAction("HMD Rotation", binding: "<XRHMD>/centerEyeRotation"));
        driver.enabled = true;
    }
}
