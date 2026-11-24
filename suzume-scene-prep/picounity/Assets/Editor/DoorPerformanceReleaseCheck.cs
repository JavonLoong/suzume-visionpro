using System.IO;
public static class DoorPerformanceReleaseCheck
{
    public static void Run()
    {
        string original=Directory.GetCurrentDirectory();
        try
        {
            Directory.SetCurrentDirectory("D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity");
            DoorAdjustmentTrialCheck.Run();
        }
        finally { Directory.SetCurrentDirectory(original); }
        BuildPicoApk.Build();
    }
}
