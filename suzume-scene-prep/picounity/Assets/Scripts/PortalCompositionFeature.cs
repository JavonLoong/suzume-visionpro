using System;
using System.Runtime.InteropServices;
using UnityEngine;
using UnityEngine.XR.OpenXR.Features;
#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.XR.OpenXR.Features;
#endif

#if UNITY_EDITOR
[OpenXRFeature(UiName="透视画面合成检查",BuildTargetGroups=new[]{BuildTargetGroup.Android},Company="Suzume",
    Desc="Inspect final frame layers and preserve projection alpha over passthrough.",Version="1.0.0",Priority=-1000,
    FeatureId=featureId)]
#endif
public sealed class PortalCompositionFeature : OpenXRFeature
{
    public const string featureId="com.suzume.portal.composition";
    protected override IntPtr HookGetInstanceProcAddr(IntPtr original)
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        return Portal_Hook(original);
#else
        return original;
#endif
    }
    [DllImport("PortalPassthrough",CallingConvention=CallingConvention.Cdecl)]
    static extern IntPtr Portal_Hook(IntPtr original);
}
