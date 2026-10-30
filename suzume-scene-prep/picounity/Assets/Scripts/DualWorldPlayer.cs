using UnityEngine;

/// <summary>
/// 头显里的双世界操作：右手握把推开或关上庭院门与异世界门。
/// 人走到门洞平面内侧时，PortalManager 会自己把视野从「只看见门洞」切成整片异世界。
/// </summary>
public class DualWorldPlayer : MonoBehaviour
{
    PortalManager _portal;
    bool _gripWas, _trackedWas;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if (Application.isEditor || Application.platform != RuntimePlatform.Android)
            return;
        new GameObject("DualWorldPlayer").AddComponent<DualWorldPlayer>();
    }

    void Update()
    {
        if (_portal == null)
            _portal = FindObjectOfType<PortalManager>();
        if (_portal == null)
            return;

        var hand = PortalControllerInput.Read(true);
        bool grip = hand.tracked && hand.grip;
        var calibration = DoorCornerMarker.Instance;
        if (grip && !_gripWas && _trackedWas && (calibration == null || (calibration.IsBrowsing && !calibration.IsBusy)))
        {
            _portal.ToggleDoorOpen(!_portal.targetDoorOpen);
            calibration?.Notice(_portal.targetDoorOpen ? "door_open" : "door_closed", 2f);
            PortalControllerInput.Pulse(true);
        }
        _gripWas = grip;
        _trackedWas = hand.tracked;
    }

}
