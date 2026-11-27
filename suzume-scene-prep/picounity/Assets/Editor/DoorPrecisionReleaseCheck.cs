using System;
using System.IO;
using UnityEngine;

public static class DoorPrecisionReleaseCheck
{
    public static void Run()
    {
        DoorCaptureTimingCheck.Run();
        string previous=Directory.GetCurrentDirectory();
        string source=Environment.GetEnvironmentVariable("SUZUME_SOURCE_PROJECT");
        try
        {
            Directory.SetCurrentDirectory("D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity");
            Environment.SetEnvironmentVariable("SUZUME_SOURCE_PROJECT",Directory.GetCurrentDirectory());
            PhysicalApertureTrialCheck.Run();
        }
        finally{Directory.SetCurrentDirectory(previous);Environment.SetEnvironmentVariable("SUZUME_SOURCE_PROJECT",source);}
        Debug.Log("[DoorPrecisionReleaseCheck] capture timing, input flow and aperture checks passed. Physical headset registration remains unverified.");
        BuildPicoApk.BuildSeparateTrial();
    }
}
