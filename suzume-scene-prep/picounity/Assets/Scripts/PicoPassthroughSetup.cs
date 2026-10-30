using System;
using UnityEngine;
#if PICO_OPENXR_SDK
using Unity.XR.OpenXR.Features.PICOSupport;
#endif

/// Keep the physical room visible behind the point markers and portal.
[DefaultExecutionOrder(10000)]
public class PicoPassthroughSetup : MonoBehaviour
{
    public bool enablePassthrough = true;
    public static bool IsReady { get; private set; }
    static float _nextAttempt;
    static string _lastError;
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        IsReady = false; _nextAttempt = 0; _lastError = null;
        if (Application.isEditor || Application.platform != RuntimePlatform.Android) return;
        if (FindObjectOfType<PicoPassthroughSetup>() == null)
            new GameObject("RealWorldPassthrough").AddComponent<PicoPassthroughSetup>();
    }
    public static void ConfigureCamera(Camera camera)
    {
        if (camera == null) return;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = Color.clear;
        // The scene's HDR intermediate target can discard alpha before OpenXR composition.
        camera.allowHDR = false;
    }
    public static bool RequestEnable()
    {
        ConfigureCamera(Camera.main);
#if UNITY_ANDROID && !UNITY_EDITOR && PICO_OPENXR_SDK
        try
        {
            if (!PassthroughFeature.isExtensionEnable || !PassthroughFeature.IsPassthroughSupported())
                throw new InvalidOperationException("OpenXR passthrough is not available yet");
            // This creates/initializes the full-screen underlay. Start alone does not.
            bool wasReady=IsReady;
            IsReady = PassthroughFeature.EnsureVideoSeeThrough();
            if(!IsReady) throw new InvalidOperationException("native initialization/full-screen layer creation failed; retrying");
            if(!wasReady) Debug.Log("[Passthrough] native underlay initialized; camera HDR="+Camera.main.allowHDR+", alpha="+Camera.main.backgroundColor.a+", graphics="+SystemInfo.graphicsDeviceType+"; visible feed still needs wearer verification");
            if(!wasReady) Debug.Log("[Passthrough] eye texture format="+UnityEngine.XR.XRSettings.eyeTextureDesc.graphicsFormat+", size="+UnityEngine.XR.XRSettings.eyeTextureWidth+"x"+UnityEngine.XR.XRSettings.eyeTextureHeight);
            _lastError = null;
            return IsReady;
        }
        catch (Exception e)
        {
            IsReady = false;
            if (_lastError != e.Message) Debug.LogWarning("[Passthrough] " + e.Message);
            _lastError = e.Message;
        }
#endif
        return false;
    }
    void Start() { if (enablePassthrough) RequestEnable(); }
    void LateUpdate()
    {
        if (Application.isEditor || Application.platform != RuntimePlatform.Android) return;
        bool required = enablePassthrough || (DoorCornerMarker.Instance != null && DoorCornerMarker.Instance.IsEditing);
        if (!required) return;
        ConfigureCamera(Camera.main);
        if (!IsReady && Time.unscaledTime >= _nextAttempt)
        {
            _nextAttempt = Time.unscaledTime + .5f;
            RequestEnable();
        }
    }
    void OnApplicationPause(bool paused)
    {
        IsReady = false; _nextAttempt = 0;
        if (!paused && enablePassthrough) RequestEnable();
    }
    void OnApplicationFocus(bool focused)
    {
        if (!focused) IsReady = false;
        else { _nextAttempt = 0; if (enablePassthrough) RequestEnable(); }
    }
}
