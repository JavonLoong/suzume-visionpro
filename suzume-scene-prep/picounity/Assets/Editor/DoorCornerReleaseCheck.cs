using System;
using System.IO;
using UnityEngine;

public static class DoorCornerReleaseCheck
{
    public static void Run()
    {
        DoorCornerRefinerCheck.Run();
        string previous=Directory.GetCurrentDirectory(),source=Environment.GetEnvironmentVariable("SUZUME_SOURCE_PROJECT");
        try
        {
            Directory.SetCurrentDirectory("D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity");
            Environment.SetEnvironmentVariable("SUZUME_SOURCE_PROJECT",Directory.GetCurrentDirectory());
            PhysicalApertureTrialCheck.Run();
        }
        finally{Directory.SetCurrentDirectory(previous);Environment.SetEnvironmentVariable("SUZUME_SOURCE_PROJECT",source);}
        Debug.Log("[DoorCornerReleaseCheck] local model, pipeline and aperture checks passed; hardware accuracy/latency remains unverified.");
        BuildPicoApk.BuildSeparateTrial();
    }
}
