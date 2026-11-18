using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Unity.Barracuda;
using UnityEngine;

// Unity.exe -batchmode -quit -executeMethod DoorDetectorTrialCheck.Run
// Runs the in-app detector on rendered images and compares it with the Python reference
// (door-keypoint-model-20261118/unity_reference.txt, written by evaluate.py --dump).
public static class DoorDetectorTrialCheck
{
    const string Reference = "../door-keypoint-model-20261118/unity_reference.txt";
    static void Require(bool ok, string message) { if (!ok) throw new Exception(message); }

    public static void Run()
    {
        string[] lines = File.ReadAllLines(Path.GetFullPath(Reference));
        string declaredRoot = lines[0];
        string referenceFolder = Path.GetDirectoryName(Path.GetFullPath(Reference)) ?? ".";
        string root = Path.IsPathRooted(declaredRoot)
            ? declaredRoot
            : Path.GetFullPath(Path.Combine(referenceFolder, declaredRoot));
        Require(Directory.Exists(root), "dataset missing: " + root);
        foreach (var type in new[] { WorkerFactory.Type.CSharpBurst, WorkerFactory.Type.ComputePrecompiled })
        {
            if (type == WorkerFactory.Type.ComputePrecompiled && !SystemInfo.supportsComputeShaders)
            { Debug.Log("[DoorDetectorTrialCheck] no compute shaders here, GPU worker skipped"); continue; }
            var detector = BarracudaDoorDetector.Create(type);
            Require(detector != null, "detector did not start");
            var texture = new Texture2D(2, 2);
            var frame = new DoorCameraFrame();
            var pixels = new Vector2[4]; var confidence = new float[4];
            var toPython = new List<float>(); var toLabel = new List<float>();
            int agree = 0, disagree = 0, doors = 0; double milliseconds = 0; int timed = 0;
            for (int n = 1; n < lines.Length; n++)
            {
                // name python_found has_label then 8 python pixels, 8 label pixels
                string[] part = lines[n].Split(' ');
                if (part.Length < 3) continue;
                bool pythonFound = part[1] == "1", labelled = part[2] == "1";
                Require(texture.LoadImage(File.ReadAllBytes(Path.Combine(root, "images", part[0] + ".jpg"))), "cannot read " + part[0]);
                var colors = texture.GetPixels32(); int w = texture.width, h = texture.height;
                if (frame.gray == null || frame.gray.Length != w * h) frame.gray = new byte[w * h];
                for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
                { var c = colors[(h - 1 - y) * w + x]; frame.gray[y * w + x] = (byte)((c.r * 77 + c.g * 150 + c.b * 29 + 128) >> 8); }
                frame.width = w; frame.height = h; frame.time = n * 100f; // far apart: every image is a new search
                var watch = System.Diagnostics.Stopwatch.StartNew();
                bool found = detector.TryDetect(frame, pixels, confidence);
                watch.Stop();
                if (n > 3) { milliseconds += watch.Elapsed.TotalMilliseconds / detector.LastPasses; timed++; }
                if (found == pythonFound) agree++; else disagree++;
                if (!found) continue;
                float worstPython = 0, worstLabel = 0;
                for (int k = 0; k < 4; k++)
                {
                    if (pythonFound) worstPython = Mathf.Max(worstPython, Vector2.Distance(pixels[k], Point(part, 3 + 2 * k)));
                    if (labelled) worstLabel = Mathf.Max(worstLabel, Vector2.Distance(pixels[k], Point(part, 11 + 2 * k)));
                }
                if (pythonFound) toPython.Add(worstPython);
                if (labelled) { toLabel.Add(worstLabel); doors++; }
            }
            UnityEngine.Object.DestroyImmediate(texture);
            detector.Dispose();
            toPython.Sort(); toLabel.Sort();
            Require(toPython.Count >= 20, "too few detections: " + toPython.Count);
            float P(List<float> v, float q) => v[Mathf.Min(v.Count - 1, (int)(v.Count * q))];
            Debug.Log($"[DoorDetectorTrialCheck] {type}: images {lines.Length - 1}, found/not-found agrees with Python {agree}, differs {disagree}; "
                + $"worst corner vs Python median {P(toPython, .5f):F3} p90 {P(toPython, .9f):F3} max {toPython[toPython.Count - 1]:F3} px; "
                + $"vs labels (n={doors}) median {P(toLabel, .5f):F3} p90 {P(toLabel, .9f):F3} px; {milliseconds / Math.Max(1, timed):F1} ms per network pass on this PC");
            Require(P(toPython, .5f) < .3f && P(toPython, .9f) < 1f, "in-app detector does not reproduce the Python result");
            Require(disagree <= Mathf.Max(2, (lines.Length - 1) / 25), "found/not-found differs from Python too often");
        }
        Debug.Log("[DoorDetectorTrialCheck] ALL CHECKS PASSED");
    }

    static Vector2 Point(string[] part, int at) =>
        new Vector2(float.Parse(part[at], CultureInfo.InvariantCulture), float.Parse(part[at + 1], CultureInfo.InvariantCulture));
}
