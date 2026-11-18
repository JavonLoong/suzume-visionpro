using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using UnityEditor.SceneManagement;
using UnityEngine;

// Unity.exe -batchmode -quit -executeMethod DoorVisionTrialCheck.Run
// Cross-checks the door pose code against the Blender-rendered dataset in ../door-keypoint-dataset-20261118.
public static class DoorVisionTrialCheck
{
    const string Dataset = "../door-keypoint-dataset-20261118";
    const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
    static void Require(bool ok, string message) { if (!ok) throw new Exception(message); }
    static System.Random _random;
    static float Gauss(float sigma)
    {
        double u = 1 - _random.NextDouble(), v = _random.NextDouble();
        return (float)(Math.Sqrt(-2 * Math.Log(u)) * Math.Cos(2 * Math.PI * v)) * sigma;
    }
    class Label
    {
        public string image; public float fx, fy, cx, cy, width, height;
        public Vector2[] pixels = new Vector2[4]; public int[] visible = new int[4];
        public Matrix4x4 cameraToDoor;
    }
    static double[] Numbers(string json, string key, int count)
    {
        int at = json.IndexOf("\"" + key + "\"", StringComparison.Ordinal);
        Require(at >= 0, "label key " + key);
        var matches = Regex.Matches(json.Substring(at + key.Length + 2), @"-?\d+(\.\d+)?([eE][-+]?\d+)?");
        var values = new double[count];
        for (int i = 0; i < count; i++) values[i] = double.Parse(matches[i].Value, CultureInfo.InvariantCulture);
        return values;
    }
    static List<Label> Load()
    {
        string root = Path.GetFullPath(Dataset);
        Require(Directory.Exists(root), "dataset missing: " + root);
        var labels = new List<Label>();
        foreach (string file in Directory.GetFiles(Path.Combine(root, "labels"), "*.json"))
        {
            string json = File.ReadAllText(file);
            double[] k = Numbers(json, "K", 9), r = Numbers(json, "R", 9), t = Numbers(json, "t", 3), p = Numbers(json, "keypoints", 12);
            var label = new Label { fx = (float)k[0], cx = (float)k[2], fy = (float)k[4], cy = (float)k[5],
                width = (float)Numbers(json, "opening_width_m", 1)[0], height = (float)Numbers(json, "opening_height_m", 1)[0],
                image = Path.Combine(root, Regex.Match(json, "\"image\": \"([^\"]+)\"").Groups[1].Value) };
            for (int i = 0; i < 4; i++) { label.pixels[i] = new Vector2((float)p[i * 3], (float)p[i * 3 + 1]); label.visible[i] = (int)p[i * 3 + 2]; }
            // Labels: X_cv = R X_door + t (OpenCV camera, right-handed door axes). Unity door axes mirror X,
            // Unity camera axes mirror Y, so M = F R D maps Unity-door to Unity-camera coordinates.
            var m = Matrix4x4.identity;
            double[] f = { 1, -1, 1 }, d = { -1, 1, 1 };
            for (int row = 0; row < 3; row++)
            {
                for (int column = 0; column < 3; column++) m[row, column] = (float)(f[row] * r[row * 3 + column] * d[column]);
                m[row, 3] = (float)(f[row] * t[row]);
            }
            label.cameraToDoor = m.inverse;
            labels.Add(label);
        }
        Require(labels.Count >= 100, "too few labels: " + labels.Count);
        return labels;
    }
    static DoorPoseSolver.Observation Observe(Label label, float sigma)
    {
        var o = new DoorPoseSolver.Observation { cameraToWorld = label.cameraToDoor, fx = label.fx, fy = label.fy, cx = label.cx, cy = label.cy };
        var p = new Vector2[4];
        for (int i = 0; i < 4; i++) p[i] = label.pixels[i] + new Vector2(Gauss(sigma), Gauss(sigma));
        o.SetPixels(p);
        return o;
    }
    static float Median(List<float> values) { values.Sort(); return values[values.Count / 2]; }
    static float Max(List<float> values) { float m = 0; foreach (float v in values) m = Mathf.Max(m, v); return m; }

    public static void Run()
    {
        _random = new System.Random(20261118);
        var labels = Load();
        var complete = labels.FindAll(l => l.visible[0] > 0 && l.visible[1] > 0 && l.visible[2] > 0 && l.visible[3] > 0);

        // 1. Exact labels: the door must come out at the origin with identity rotation.
        var position = new List<float>(); var angle = new List<float>(); var uprightPosition = new List<float>();
        foreach (var label in complete)
        {
            var o = Observe(label, 0);
            Require(DoorPoseSolver.SolveSingle(o, label.width, label.height, out var s), "single solve failed " + label.image);
            position.Add(s.position.magnitude * 1000); angle.Add(Quaternion.Angle(s.rotation, Quaternion.identity));
            Require(DoorPoseSolver.SolveUpright(new[] { o }, label.width, label.height, s, out var u), "upright solve failed " + label.image);
            uprightPosition.Add(u.position.magnitude * 1000);
            Require(Mathf.Abs(Mathf.DeltaAngle(u.yawDegrees, 0)) < .5f, "upright yaw " + u.yawDegrees + " " + label.image);
        }
        Debug.Log($"[DoorVisionTrialCheck] exact labels n={complete.Count}: 6-DOF position median {Median(position):F4} mm max {Max(position):F4} mm, rotation max {Max(angle):F4} deg; upright position max {Max(uprightPosition):F4} mm");
        Require(Max(position) < .5f && Max(angle) < .5f && Max(uprightPosition) < .5f, "exact labels do not reproduce the Blender pose");

        // 2. Half-pixel noise on single views: what one frame can and cannot give.
        position.Clear(); uprightPosition.Clear(); angle.Clear();
        foreach (var label in complete)
        {
            var o = Observe(label, .5f);
            if (!DoorPoseSolver.SolveSingle(o, label.width, label.height, out var s)) continue;
            position.Add(s.position.magnitude * 1000); angle.Add(Quaternion.Angle(s.rotation, Quaternion.identity));
            if (DoorPoseSolver.SolveUpright(new[] { o }, label.width, label.height, s, out var u)) uprightPosition.Add(u.position.magnitude * 1000);
        }
        float single = Median(position), upright = Median(uprightPosition);
        Debug.Log($"[DoorVisionTrialCheck] 0.5 px noise, one view: 6-DOF median {single:F2} mm / {Median(angle):F1} deg (max {Max(position):F1} mm); upright median {upright:F2} mm (max {Max(uprightPosition):F1} mm)");
        Require(upright <= single, "upright constraint did not help");

        // 3. Several noisy views of a door from a moving head: lock, then notice a moved door.
        float w = DoorPhysicalSize.Presets[1].width, h = DoorPhysicalSize.Presets[1].height;
        var stabilizer = new DoorPoseStabilizer();
        Vector3 door = new Vector3(.3f, .75f, .5f); float yaw = 37f; float time = 0;
        int lockedAt = -1;
        for (int i = 0; i < 40 && lockedAt < 0; i++)
            if (stabilizer.Add(Simulate(door, yaw, w, h, time += .15f, .7f), w, h) == DoorPoseStabilizer.Event.Locked) lockedAt = i;
        Require(lockedAt >= 0, "stabilizer never locked");
        var locked = stabilizer.LockedSolution;
        float lockError = Vector3.Distance(locked.position, door) * 1000, yawError = Mathf.Abs(Mathf.DeltaAngle(locked.yawDegrees, yaw));
        Debug.Log($"[DoorVisionTrialCheck] multi-view lock after {lockedAt + 1} frames: position error {lockError:F2} mm, yaw error {yawError:F2} deg, rms {locked.rmsPixels:F2} px");
        Require(lockError < 3f && yawError < 4f, "multi-view lock is inaccurate");
        for (int i = 0; i < 30; i++)
            Require(stabilizer.Add(Simulate(door, yaw, w, h, time += .15f, .7f), w, h) == DoorPoseStabilizer.Event.None, "still door reported as moved or re-locked");
        Vector3 moved = door + new Vector3(.015f, 0, .01f);
        bool drifted = false; int relocked = -1;
        for (int i = 0; i < 60 && relocked < 0; i++)
        {
            var change = stabilizer.Add(Simulate(moved, yaw, w, h, time += .15f, .7f), w, h);
            drifted |= change == DoorPoseStabilizer.Event.Drifted;
            if (change == DoorPoseStabilizer.Event.Locked) relocked = i;
        }
        Require(drifted && relocked >= 0, "moved door was not noticed and re-locked");
        float relockError = Vector3.Distance(stabilizer.LockedSolution.position, moved) * 1000;
        Debug.Log($"[DoorVisionTrialCheck] moved door re-locked after {relocked + 1} frames: position error {relockError:F2} mm");
        Require(relockError < 3f, "re-lock is inaccurate");
        // A door that disappears for longer than the timeout starts a new search.
        var lost = new DoorPoseStabilizer();
        lost.Add(Simulate(door, yaw, w, h, 1f, .7f), w, h); lost.MarkMissing(1.5f);
        Require(lost.CurrentState == DoorPoseStabilizer.State.Sampling, "short gap reset the sampling");
        lost.MarkMissing(2.5f);
        Require(lost.CurrentState == DoorPoseStabilizer.State.Searching, "lost door kept old samples");

        // 4. Edge refinement on the rendered images.
        var before = new List<float>(); var after = new List<float>(); var bias = new List<float>();
        var texture = new Texture2D(2, 2);
        var noisy = new Vector2[4]; var refined = new Vector2[4];
        int improved = 0;
        foreach (var label in labels)
        {
            if (Array.Exists(label.visible, v => v != 2) || Vector2.Distance(label.pixels[0], label.pixels[2]) < 40) continue;
            Require(texture.LoadImage(File.ReadAllBytes(label.image)), "cannot read " + label.image);
            var colors = texture.GetPixels32(); int tw = texture.width, th = texture.height;
            var gray = new byte[tw * th];
            for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++)
            { var c = colors[(th - 1 - y) * tw + x]; gray[y * tw + x] = (byte)((c.r * 77 + c.g * 150 + c.b * 29) >> 8); }
            float sigma = Mathf.Clamp(Vector2.Distance(label.pixels[0], label.pixels[1]) * .025f, .7f, 3f);
            for (int i = 0; i < 4; i++) noisy[i] = label.pixels[i] + new Vector2(Gauss(sigma), Gauss(sigma));
            DoorEdgeRefiner.Refine(gray, tw, th, noisy, refined);
            float e0 = 0, e1 = 0, e2 = 0;
            for (int i = 0; i < 4; i++) { e0 += Vector2.Distance(noisy[i], label.pixels[i]) / 4; e1 += Vector2.Distance(refined[i], label.pixels[i]) / 4; }
            DoorEdgeRefiner.Refine(gray, tw, th, label.pixels, refined);
            for (int i = 0; i < 4; i++) e2 += Vector2.Distance(refined[i], label.pixels[i]) / 4;
            before.Add(e0); after.Add(e1); bias.Add(e2); if (e1 < e0) improved++;
        }
        UnityEngine.Object.DestroyImmediate(texture);
        Debug.Log($"[DoorVisionTrialCheck] edge refinement n={before.Count}: corner error median {Median(before):F2} -> {Median(after):F2} px, improved {improved}/{before.Count}, shift applied to exact corners median {Median(bias):F2} px");

        // The manual four-corner fallback must also accept a door of this size, with hand-pointing error.
        var manual = new[] { new Vector3(w * .5f, .75f, 0), new Vector3(-w * .5f, .752f, .001f), new Vector3(w * .5f + .002f, .75f + h, .002f), new Vector3(-w * .5f, .751f + h, -.002f) };
        Require(DoorCalibrationMath.TryFit(manual, new Vector3(0, 1.1f, .4f), out var manualFit, out _), "manual fit rejects the printed door");
        Require(Mathf.Abs(manualFit.width - w) < .002f && Mathf.Abs(manualFit.height - h) < .003f, "manual fit size");
        manual[3].y += h * .6f;
        Require(!DoorCalibrationMath.TryFit(manual, new Vector3(0, 1.1f, .4f), out _, out _), "manual fit accepts a lopsided small door");

        // 5. The found pose reaches the existing preview/confirm flow at the printed door's real size.
        string sizeKey = "SuzumePortal.DoorSize.V1"; bool hadSize = PlayerPrefs.HasKey(sizeKey); string savedSize = PlayerPrefs.GetString(sizeKey, "");
        try
        {
            DoorPhysicalSize.Select(0); DoorPhysicalSize.Cycle();
            Require(DoorPhysicalSize.Index == 1 && Mathf.Approximately(DoorPhysicalSize.Width, w), "size preset cycling");
            DoorPhysicalSize.Cycle(); DoorPhysicalSize.Cycle();
            Require(DoorPhysicalSize.Index == 0, "size presets do not wrap");
            Require(DoorPhysicalSize.SetCustom(.03f, .07f) && DoorPhysicalSize.Index == DoorPhysicalSize.CustomIndex && Mathf.Approximately(DoorPhysicalSize.Height, .07f), "custom size");
            Require(!DoorPhysicalSize.SetCustom(0, 1), "invalid custom size accepted");
        }
        finally { if (hadSize) PlayerPrefs.SetString(sizeKey, savedSize); else PlayerPrefs.DeleteKey(sizeKey); PlayerPrefs.Save(); }

        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal = UnityEngine.Object.FindObjectOfType<PortalManager>(); portal.BuildPortal();
        Camera.main.transform.position = new Vector3(0, 1.1f, .4f);
        var marker = new GameObject("DoorVisionCheck").AddComponent<DoorCornerMarker>();
        marker.GetType().GetMethod("Start", Private).Invoke(marker, null);
        var rotation = Quaternion.Euler(0, 20, 0); var centre = new Vector3(.1f, .8f, 0);
        Require(marker.PreviewAutomaticPlacement(centre, rotation, w, h), "automatic preview refused");
        Require(marker.IsEditing && portal.calibrationHidden, "automatic preview must wait for confirmation with the world hidden");
        Require(Mathf.Approximately(portal.portalWidth, w) && Mathf.Approximately(portal.portalHeight, h) && portal.portalPosition == centre, "portal did not take the detected size and place");
        Require(Mathf.Abs(portal.transform.localScale.y - h / PortalConfig.BaseDoorHeight) < 1e-6f, "portal scale is clamped above the printed door");
        var corners = (Vector3[])marker.GetType().GetField("_corners", Private).GetValue(marker);
        Require(Vector3.Distance(corners[0], corners[1]) is float cw && Mathf.Abs(cw - w) < 1e-5f && Mathf.Abs((corners[2] - corners[0]).y - h) < 1e-5f, "preview outline size");
        Require(Vector3.Dot(corners[0] - corners[1], rotation * Vector3.right) > 0, "bottom-left must be on the portal's +X side");
        Require(!marker.PreviewAutomaticPlacement(centre, rotation, w, h), "second proposal must not replace a pending preview");
        var hand = new PortalControllerInput.Hand { tracked = true };
        var process = marker.GetType().GetMethod("ProcessInput", Private);
        process.Invoke(marker, new object[] { hand, hand });
        var pressed = hand; pressed.trigger = true;
        process.Invoke(marker, new object[] { hand, pressed }); // left trigger rejects the proposal
        Require(!marker.IsEditing && !marker.IsBrowsing && portal.calibrationHidden, "rejecting the proposal must return to the reality-only ready state");
        UnityEngine.Object.DestroyImmediate(marker.gameObject);

        StablePlacementTrialCheck.Run();
        Debug.Log("[DoorVisionTrialCheck] ALL CHECKS PASSED");
    }

    // A head-mounted camera about 35 cm in front of the door, wandering a few centimetres.
    static DoorPoseSolver.Observation Simulate(Vector3 door, float yaw, float width, float height, float time, float sigma)
    {
        var rotation = Quaternion.Euler(0, yaw, 0);
        Vector3 centre = door + Vector3.up * height * .5f;
        Vector3 eye = centre + rotation * new Vector3(Gauss(.06f), .12f + Gauss(.03f), .35f + Gauss(.03f));
        var look = Quaternion.LookRotation(centre - eye + new Vector3(Gauss(.02f), Gauss(.02f), Gauss(.02f)), Vector3.up);
        var o = new DoorPoseSolver.Observation { cameraToWorld = Matrix4x4.TRS(eye, look, Vector3.one), fx = 900, fy = 900, cx = 640, cy = 480, time = time };
        var pixels = new Vector2[4];
        for (int k = 0; k < 4; k++)
        {
            Vector3 world = door + rotation * new Vector3((k % 2 == 0 ? 1 : -1) * width * .5f, k >= 2 ? height : 0, 0);
            Vector3 p = o.cameraToWorld.inverse.MultiplyPoint3x4(world);
            pixels[k] = new Vector2(o.fx * p.x / p.z + o.cx + Gauss(sigma), o.cy - o.fy * p.y / p.z + Gauss(sigma));
        }
        o.SetPixels(pixels);
        return o;
    }
}
