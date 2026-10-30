using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.XR.Management;
using Unity.XR.PXR;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features.Interactions;

/// <summary>
/// 命令行入口：Unity.exe -executeMethod BuildPicoApk.Build
/// </summary>
public static class BuildPicoApk
{
    const string PackageId = "com.suzume.portal";
    const string ApkPath = "Builds/SuzumePortal-PICO.apk";

    public static void Build()
    {
        Directory.CreateDirectory("Builds");

        var androidRoot = Path.GetFullPath(Path.Combine(EditorApplication.applicationContentsPath, "PlaybackEngines/AndroidPlayer"));
        var sdk = Path.Combine(androidRoot, "SDK");
        var ndk = Path.Combine(androidRoot, "NDK", "android-ndk-r23b");
        var jdk = Path.Combine(androidRoot, "OpenJDK");
        UnityEditor.Android.AndroidExternalToolsSettings.sdkRootPath = sdk;
        UnityEditor.Android.AndroidExternalToolsSettings.ndkRootPath = ndk;
        UnityEditor.Android.AndroidExternalToolsSettings.jdkRootPath = jdk;

        if (!EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android))
            Fail("无法切换到 Android 构建目标");

        PlayerSettings.companyName = "Suzume";
        PlayerSettings.productName = "Suzume Portal";
        PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.Android, PackageId);
        PlayerSettings.bundleVersion = "1.11";
        PlayerSettings.Android.bundleVersionCode = 12;
        PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
        PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel29;
        PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevel34;
        PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
        PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[]
        {
            GraphicsDeviceType.Vulkan
        });
        PlayerSettings.defaultInterfaceOrientation = UIOrientation.LandscapeLeft;
        PlayerSettings.allowedAutorotateToPortrait = false;
        PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
        PlayerSettings.allowedAutorotateToLandscapeLeft = true;
        PlayerSettings.allowedAutorotateToLandscapeRight = true;
        PlayerSettings.SetManagedStrippingLevel(BuildTargetGroup.Android, ManagedStrippingLevel.Minimal);
        PlayerSettings.stripEngineCode = true;
        PlayerSettings.preserveFramebufferAlpha = true;

        var compositionPlugin=AssetImporter.GetAtPath("Assets/Plugins/Android/arm64-v8a/libPortalPassthrough.so") as PluginImporter;
        if(compositionPlugin==null) Fail("Missing native composition plugin; run Native~/PortalPassthrough/build.ps1");
        compositionPlugin.SetCompatibleWithAnyPlatform(false);
        compositionPlugin.SetCompatibleWithPlatform(BuildTarget.Android,true);
        compositionPlugin.SetPlatformData(BuildTarget.Android,"CPU","ARM64");
        compositionPlugin.SaveAndReimport();

        EnableOpenXR();
        EnsurePicoSettings();
        EnsureMarkMaterial();

        EditorUserBuildSettings.androidBuildSystem = AndroidBuildSystem.Gradle;
        EditorUserBuildSettings.exportAsGoogleAndroidProject = false;
        EditorUserBuildSettings.development = false;

        var options = new BuildPlayerOptions
        {
            scenes = new[] { "Assets/Scenes/SuzumePortal.unity" },
            locationPathName = ApkPath,
            target = BuildTarget.Android,
            targetGroup = BuildTargetGroup.Android,
            options = BuildOptions.CompressWithLz4
        };

        var report = BuildPipeline.BuildPlayer(options);
        if (report.summary.result != BuildResult.Succeeded)
            Fail("打包失败: " + report.summary.result + " 错误数 " + report.summary.totalErrors);

        Debug.Log("APK 已生成: " + Path.GetFullPath(ApkPath) + " 大小 " + report.summary.totalSize);
    }

    static void EnableOpenXR()
    {
        UnityEditor.XR.OpenXR.Features.FeatureHelpers.RefreshFeatures(BuildTargetGroup.Android);
        var general = LoadOrCreateXrSettings();
        if (!general.HasSettingsForBuildTarget(BuildTargetGroup.Android))
            general.CreateDefaultSettingsForBuildTarget(BuildTargetGroup.Android);
        if (!general.HasManagerSettingsForBuildTarget(BuildTargetGroup.Android))
            general.CreateDefaultManagerSettingsForBuildTarget(BuildTargetGroup.Android);

        var manager = general.SettingsForBuildTarget(BuildTargetGroup.Android).Manager;
        if (!XRPackageMetadataStore.AssignLoader(manager, "OpenXRLoader", BuildTargetGroup.Android))
            Debug.LogWarning("OpenXRLoader 可能已经启用，继续打包");

        var openXr = OpenXRSettings.GetSettingsForBuildTargetGroup(BuildTargetGroup.Android);
        if (openXr == null)
            Fail("找不到 Android 的 OpenXR 设置");

        openXr.renderMode = OpenXRSettings.RenderMode.MultiPass;
        EnablePicoFeatures(openXr);
        if(openXr.GetFeature<PortalCompositionFeature>()==null || !openXr.GetFeature<PortalCompositionFeature>().enabled)
            Fail("Final composition diagnostics feature was not enabled");

        EditorUtility.SetDirty(openXr);
        EditorUtility.SetDirty(manager);
        AssetDatabase.SaveAssets();
    }

    static void EnsurePicoSettings()
    {
        if (EditorBuildSettings.TryGetConfigObject("Unity.XR.PXR.Settings", out PXR_Settings existing) && existing != null)
            return;
        var settings = ScriptableObject.CreateInstance<PXR_Settings>();
        settings.stereoRenderingModeAndroid = PXR_Settings.StereoRenderingModeAndroid.MultiPass;
        AssetDatabase.CreateAsset(settings, "Assets/XR/PXR_Settings.asset");
        EditorBuildSettings.AddConfigObject("Unity.XR.PXR.Settings", settings, true);
        AssetDatabase.SaveAssets();
    }

    static void EnsureMarkMaterial()
    {
        var shader = AssetDatabase.LoadAssetAtPath<Shader>("Assets/Shaders/MarkLabel.shader");
        if (shader == null)
            Fail("找不到标点着色器");
        const string path = "Assets/Resources/DoorMark/MarkLabel.mat";
        var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (mat == null)
        {
            mat = new Material(shader) { name = "MarkLabel" };
            AssetDatabase.CreateAsset(mat, path);
        }
        else if (mat.shader != shader)
        {
            mat.shader = shader;
            EditorUtility.SetDirty(mat);
        }
        AssetDatabase.SaveAssets();
    }

    static XRGeneralSettingsPerBuildTarget LoadOrCreateXrSettings()
    {
        var guids = AssetDatabase.FindAssets("t:XRGeneralSettingsPerBuildTarget");
        XRGeneralSettingsPerBuildTarget general = null;
        if (guids.Length > 0)
            general = AssetDatabase.LoadAssetAtPath<XRGeneralSettingsPerBuildTarget>(AssetDatabase.GUIDToAssetPath(guids[0]));
        if (general == null)
        {
            general = ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();
            AssetDatabase.CreateAsset(general, "Assets/XR/XRGeneralSettingsPerBuildTarget.asset");
        }
        EditorBuildSettings.AddConfigObject(XRGeneralSettings.k_SettingsKey, general, true);
        return general;
    }

    static void EnablePicoFeatures(OpenXRSettings openXr)
    {
        string[] ids =
        {
            PortalCompositionFeature.featureId,
            "com.unity.openxr.feature.pico",
            "com.pico.openxr.feature.spatialanchor",
            "com.pico.openxr.feature.passthrough",
            "com.unity.openxr.pico.features",
            "com.unity.openxr.feature.input.PICO4Ultratouch",
            "com.unity.openxr.feature.input.PICO4touch"
        };
        foreach (var feature in openXr.GetFeatures())
        {
            var id = feature.GetType().GetField("featureId", BindingFlags.Public | BindingFlags.Static);
            var value = id?.GetValue(null) as string;
            if (value == null) continue;
            for (int i = 0; i < ids.Length; i++)
            {
                if (value == ids[i])
                    feature.enabled = true;
            }
            if(feature is Unity.XR.OpenXR.Features.PICOSupport.PICOSpatialMesh)
                feature.enabled=false;
        }
    }

    static void Fail(string message)
    {
        Debug.LogError(message);
        EditorApplication.Exit(1);
        throw new System.Exception(message);
    }
}
