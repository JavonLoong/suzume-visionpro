using System.IO;
using UnityEditor.Android;

// Keep Unity's bundled AAR directory available after machine-wide repository mirror hooks run.
public sealed class PicoBuildRepositories : IPostGenerateGradleAndroidProject
{
    public int callbackOrder => 999;
    public void OnPostGenerateGradleAndroidProject(string path)
    {
        string settings=Path.Combine(Directory.GetParent(path).FullName,"settings.gradle");
        const string marker="// Suzume: preserve bundled Pico AARs";
        string content=File.ReadAllText(settings);
        if(!content.Contains(marker)) File.AppendAllText(settings,"\n"+marker+@"
gradle.settingsEvaluated { settings ->
    settings.dependencyResolutionManagement.repositories {
        flatDir { dirs new File(settings.settingsDir, 'unityLibrary/libs') }
    }
}
");
    }
}
