using System;
using System.Collections.Generic;
using Unity.XR.Management.AndroidManifest.Editor;
using UnityEngine.XR.OpenXR;

/// <summary>
/// 让 APK 被 PICO 系统认成沉浸式 OpenXR 应用，而不是一块二维面板。
/// </summary>
public class PicoManifest : IAndroidManifestRequirementProvider
{
    public ManifestRequirement ProvideManifestRequirement()
    {
        return new ManifestRequirement
        {
            SupportedXRLoaders = new HashSet<Type> { typeof(OpenXRLoader) },
            NewElements = new List<ManifestElement>
            {
                Feature("android.hardware.vr.headtracking"),
                Category("org.khronos.openxr.intent.category.IMMERSIVE_HMD"),
                Category("com.picovr.intent.category.VR")
            }
        };
    }

    static ManifestElement Feature(string name)
    {
        return new ManifestElement
        {
            ElementPath = new List<string> { "manifest", "uses-feature" },
            Attributes = new Dictionary<string, string>
            {
                { "name", name },
                { "required", "true" },
                { "version", "1" }
            }
        };
    }

    static ManifestElement Meta(string name, string value)
    {
        return new ManifestElement
        {
            ElementPath = new List<string> { "manifest", "application", "meta-data" },
            Attributes = new Dictionary<string, string>
            {
                { "name", name },
                { "value", value }
            }
        };
    }

    static ManifestElement Category(string name)
    {
        return new ManifestElement
        {
            ElementPath = new List<string> { "manifest", "application", "activity", "intent-filter", "category" },
            Attributes = new Dictionary<string, string> { { "name", name } }
        };
    }
}
