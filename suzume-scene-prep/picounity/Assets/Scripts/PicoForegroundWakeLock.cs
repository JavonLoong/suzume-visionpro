using System;
using UnityEngine;
using Unity.XR.PICO.TOBSupport;

// A foreground-only request. Never changes the headset's persistent sleep settings.
public sealed class PicoForegroundWakeLock : MonoBehaviour
{
    bool _paused, _focused, _bound, _binding, _held;
    int _previousTimeout, _attempts;
    float _nextBind, _nextReport;
    static bool NativeDevice => !Application.isEditor && Application.platform == RuntimePlatform.Android;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if (NativeDevice && FindObjectOfType<PicoForegroundWakeLock>() == null)
            new GameObject("ForegroundWakeLock").AddComponent<PicoForegroundWakeLock>();
    }
    void Awake()
    {
        _previousTimeout = Screen.sleepTimeout;
        _focused = Application.isFocused;
    }
    void Start() { Apply(); TryBind(); }
    void TryBind()
    {
        if (!NativeDevice || _bound || _binding || _attempts >= 3) return;
        _attempts++; _binding = true; _nextBind = Time.unscaledTime + 5f;
        try
        {
            if (!PXR_Enterprise.InitEnterpriseService(false))
                throw new InvalidOperationException("enterprise initialization failed");
            PXR_Enterprise.BindEnterpriseService(connected =>
            {
                if (this == null || !isActiveAndEnabled) return;
                _binding = false; _bound = connected;
                Debug.Log("[PortalPower] enterprise service connected=" + connected);
                Apply();
            });
        }
        catch (Exception e)
        {
            _binding = false;
            Debug.LogWarning("[PortalPower] bind: " + e.Message);
        }
    }
    void Update()
    {
        if (!NativeDevice) return;
        if (!_bound && !_binding && Time.unscaledTime >= _nextBind) TryBind();
        if (Time.unscaledTime >= _nextReport)
        {
            _nextReport = Time.unscaledTime + 15f;
            Debug.Log($"[PortalPower] alive focused={_focused} paused={_paused} enterpriseRequest={_held} screenTimeout={Screen.sleepTimeout}; " +
                (DoorCornerMarker.Instance != null ? DoorCornerMarker.Instance.ProgressSummary : "marker starting"));
        }
    }
    void Apply()
    {
        bool wanted = isActiveAndEnabled && _focused && !_paused;
        Screen.sleepTimeout = wanted ? SleepTimeout.NeverSleep : _previousTimeout;
        if (!NativeDevice || !_bound || wanted == _held) return;
        try
        {
            if (wanted) PXR_Enterprise.AcquireWakeLock();
            else PXR_Enterprise.ReleaseWakeLock();
            _held = wanted;
            Debug.Log("[PortalPower] foreground wake request=" + wanted + "; no persistent setting changed");
        }
        catch (Exception e) { Debug.LogWarning("[PortalPower] wake request: " + e.Message); }
    }
    void OnApplicationPause(bool paused)
    {
        _paused = paused;
        Debug.Log("[PortalPower] pause=" + paused);
        Apply();
    }
    void OnApplicationFocus(bool focused)
    {
        _focused = focused;
        Debug.Log("[PortalPower] focus=" + focused);
        Apply();
    }
    void OnDisable() { Apply(); }
    void OnDestroy()
    {
        _focused = false; Apply();
        if (NativeDevice && (_bound || _binding))
        {
            try { PXR_Enterprise.UnBindEnterpriseService(); }
            catch (Exception e) { Debug.LogWarning("[PortalPower] unbind: " + e.Message); }
        }
    }
}
