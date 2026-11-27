using System;
using System.IO;
using UnityEngine;
public static class IntegratedDoorReleaseCheck
{
    public static void Run()
    {
        string previous=Directory.GetCurrentDirectory();
        try
        {
            Directory.SetCurrentDirectory("D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity");
            DoorVisionTrialCheck.Run();
            PhysicalApertureTrialCheck.Run();
        }
        finally{Directory.SetCurrentDirectory(previous);}
        Debug.Log("[IntegratedDoorReleaseCheck] geometry and portal regression passed; building trial, hardware unverified.");
        BuildPicoApk.BuildSeparateTrial();
    }
}
