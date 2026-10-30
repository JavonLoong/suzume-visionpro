using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;
using UnityEngine.XR;

/// Explicit OpenXR actions keep all controller inputs active, including the face buttons.
public static class PortalControllerInput
{
    public struct Hand
    {
        public bool tracked, trigger, grip, primary, secondary;
        public Vector3 position;
        public Quaternion rotation;
    }
    static InputActionMap _actions;
    static readonly List<UnityEngine.XR.InputDevice> Devices = new List<UnityEngine.XR.InputDevice>();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    static void Bind()
    {
        _actions?.Dispose();
        _actions = new InputActionMap("PortalHands");
        foreach (string hand in new[] { "LeftHand", "RightHand" })
            foreach (string control in new[] { "devicePosition", "deviceRotation", "pointerPosition", "pointerRotation", "isTracked", "trackingState", "trigger", "triggerPressed", "grip", "gripPressed", "primaryButton", "secondaryButton" })
                _actions.AddAction(hand + control, InputActionType.PassThrough, "<XRController>{" + hand + "}/" + control);
        _actions.Enable();
    }

    public static Hand Read(bool right)
    {
        string usage = right ? "RightHand" : "LeftHand";
        foreach (var device in InputSystem.devices)
        {
            bool matches = false;
            foreach (var u in device.usages)
                matches |= string.Equals(u.ToString(), usage, StringComparison.OrdinalIgnoreCase);
            if (!matches) continue;
            var tracked = device.TryGetChildControl<ButtonControl>("isTracked");
            var state = device.TryGetChildControl<IntegerControl>("trackingState");
            if (tracked == null || !tracked.isPressed || (state != null && (state.ReadValue() & 3) != 3)) continue;
            var pos = device.TryGetChildControl<Vector3Control>("pointerPosition") ?? device.TryGetChildControl<Vector3Control>("devicePosition");
            var rot = device.TryGetChildControl<QuaternionControl>("pointerRotation") ?? device.TryGetChildControl<QuaternionControl>("deviceRotation");
            if (pos == null || rot == null) continue;
            return new Hand { tracked = true, position = pos.ReadValue(), rotation = rot.ReadValue(),
                trigger = Button(device, "triggerPressed", "trigger"), grip = Button(device, "gripPressed", "grip"),
                primary = Button(device, "primaryButton"), secondary = Button(device, "secondaryButton") };
        }
        Devices.Clear();
        InputDevices.GetDevicesWithCharacteristics(InputDeviceCharacteristics.Controller | (right ? InputDeviceCharacteristics.Right : InputDeviceCharacteristics.Left), Devices);
        foreach (var device in Devices)
        {
            if (!device.isValid || !device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.isTracked, out bool tracked) || !tracked) continue;
            if (!device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.devicePosition, out var pos) || !device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.deviceRotation, out var rot)) continue;
            var h = new Hand { tracked = true, position = pos, rotation = rot };
            device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.triggerButton, out h.trigger);
            device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.gripButton, out h.grip);
            device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.primaryButton, out h.primary);
            device.TryGetFeatureValue(UnityEngine.XR.CommonUsages.secondaryButton, out h.secondary);
            return h;
        }
        return default;
    }
    static bool Button(UnityEngine.InputSystem.InputDevice device, string name, string axis = null)
    {
        var button = device.TryGetChildControl<ButtonControl>(name);
        if (button != null && button.isPressed) return true;
        return axis != null && (device.TryGetChildControl<AxisControl>(axis)?.ReadValue() ?? 0f) > .6f;
    }
    public static Vector3 ToWorld(Vector3 point) => HeadsetBootstrap.Origin != null ? HeadsetBootstrap.Origin.TransformPoint(point) : point;
    public static Vector3 ToTracking(Vector3 point) => HeadsetBootstrap.Origin != null ? HeadsetBootstrap.Origin.InverseTransformPoint(point) : point;
    public static Quaternion ToWorld(Quaternion rot) => HeadsetBootstrap.Origin != null ? HeadsetBootstrap.Origin.rotation * rot : rot;
    public static Quaternion ToTracking(Quaternion rot) => HeadsetBootstrap.Origin != null ? Quaternion.Inverse(HeadsetBootstrap.Origin.rotation) * rot : rot;
    public static Ray AimRay(Hand hand) => new Ray(ToWorld(hand.position),ToWorld(hand.rotation)*Vector3.forward);
    public static void Pulse(bool right)
    {
        var device = InputDevices.GetDeviceAtXRNode(right ? XRNode.RightHand : XRNode.LeftHand);
        if (device.TryGetHapticCapabilities(out var caps) && caps.supportsImpulse) device.SendHapticImpulse(0, .35f, .07f);
    }
}
