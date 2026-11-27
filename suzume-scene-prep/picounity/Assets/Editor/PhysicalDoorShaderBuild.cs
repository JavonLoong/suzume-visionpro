using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Rendering;
using UnityEngine;

// The headset runs the CPU backend with CPU tensor inputs. Pixel-backend shaders
// are unused and trigger Vulkan compiler memory failures. Keep this exclusion
// tied to the actual runtime worker selection; editor/compute/portal shaders stay.
public sealed class PhysicalDoorShaderBuild : IPreprocessShaders
{
    public int callbackOrder => 0;
    public void OnProcessShader(Shader shader, ShaderSnippetData snippet, IList<ShaderCompilerData> data)
    {
        if(EditorUserBuildSettings.activeBuildTarget==BuildTarget.Android &&
            BarracudaDoorDetector.HeadsetWorkerType==Unity.Barracuda.WorkerFactory.Type.CSharpBurst &&
            shader.name.StartsWith("Barracuda/",System.StringComparison.Ordinal))
            data.Clear();
    }
}
