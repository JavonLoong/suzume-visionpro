using System;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Unity.Barracuda;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class GuidedDoorTrialCheck
{
    const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
    static void Require(bool ok, string message) { if (!ok) throw new Exception(message); }
    static object Call(object o, string name, params object[] args) => o.GetType().GetMethod(name, Private).Invoke(o, args);
    static void Set(object o, string name, object value) => o.GetType().GetField(name, Private).SetValue(o, value);
    class Detector : IDoorKeypointDetector, IDoorGuidedDetector
    {
        public int calls;
        public void Reset() { }
        public bool TryDetect(DoorCameraFrame f, Vector2[] p, float[] c) { throw new Exception("unexpected whole-frame search"); }
        public bool TryDetectGuided(DoorCameraFrame f, Rect r, Vector2[] p, float[] c) { calls++; return false; }
    }
    public static void Run()
    {
        Directory.CreateDirectory("Builds/controller-check");
        StablePlacementTrialCheck.Run();
        MathChecks();
        FlowChecks();
        int detections = NetworkChecks();
        File.WriteAllText("Builds/controller-check/guided-result.txt",
            "PASS: existing manual placement/render/controller suite; controller/camera parallax and head motion; bounded local crops; off-target and behind-ray rejection; guided entry/retarget/cancel/manual fallback; paused and late-frame guards; release-before-confirm; cancel restores previous placement. Synthetic guided network detections " + detections + "/12. Real headset recognition accuracy not established by these checks.\n");
        Debug.Log("[GuidedDoorTrialCheck] ALL CHECKS PASSED");
    }
    static void MathChecks()
    {
        var f = new DoorCameraFrame { width = 2048, height = 1536, fx = 1400, fy = 1400, cx = 1024, cy = 768, cameraToWorld = Matrix4x4.identity };
        Vector3 target = new Vector3(.02f, .04f, .6f), hand = new Vector3(.25f, -.1f, 0);
        var hint = new DoorSearchHint(); Require(hint.Set(new Ray(hand, target - hand)), "valid aim rejected");
        Vector2 pixel = new Vector2(f.cx + f.fx * target.x / target.z, f.cy - f.fy * target.y / target.z);
        bool covers = false;
        for (int i = 0; i < 8; i++)
        {
            Require(hint.TryCrop(f, .0558f, out var r), "visible aim has no crop");
            Require(r.xMin >= 0 && r.yMin >= 0 && r.xMax <= f.width + .01f && r.yMax <= f.height + .01f, "crop exceeds frame");
            Require(r.width < f.width * .8f, "guided search reverted to whole frame");
            covers |= r.Contains(pixel);
        }
        Require(covers && hint.Accepts(target, .0558f), "near target lost due to controller parallax");
        Require(!hint.Accepts(target + Vector3.right, .0558f) && !hint.Accepts(hand - (target - hand), .0558f), "off-target/behind solution accepted");
        hint.Focus(target); Require(hint.TryCrop(f, .0558f, out var before), "focus crop missing");
        f.cameraToWorld = Matrix4x4.Translate(new Vector3(.1f, 0, 0));
        Require(hint.TryCrop(f, .0558f, out var after), "moving camera crop missing");
        Require(Mathf.Abs((after.center.x - before.center.x) + f.fx * .1f / .6f) < .1f, "crop failed to follow camera translation");
        hint.Set(new Ray(Vector3.zero, Vector3.back)); Require(!hint.TryCrop(f, .0558f, out _), "behind-camera target searched");
        int revision = hint.Revision; hint.Clear(); Require(hint.Revision != revision && !hint.Active, "cancel does not invalidate frames");
    }
    static void FlowChecks()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal = UnityEngine.Object.FindObjectOfType<PortalManager>(); portal.BuildPortal();
        Camera.main.transform.position = new Vector3(0, 1.6f, 2);
        var marker = new GameObject("GuidedFlowCheck").AddComponent<DoorCornerMarker>(); Call(marker, "Start");
        var previous = DoorAutoLocator.Detector; var fake = new Detector(); DoorAutoLocator.Detector = fake;
        var locator = new GameObject("GuidedLocatorCheck").AddComponent<DoorAutoLocator>(); Call(locator, "Awake");
        var setter = typeof(PicoPassthroughSetup).GetProperty("IsReady").GetSetMethod(true); bool ready = PicoPassthroughSetup.IsReady;
        setter.Invoke(null, new object[] { true });
        var r = new PortalControllerInput.Hand { tracked = true, position = new Vector3(.2f, 1, 2), rotation = Quaternion.LookRotation(Vector3.back) };
        var l = new PortalControllerInput.Hand { tracked = true };
        void Send() => Call(marker, "ProcessInput", r, l);
        try
        {
            Send(); r.trigger = true; Send();
            Require(marker.IsGuiding && locator.hint.Active && portal.calibrationHidden, "first trigger did not enter guided search");
            Require(marker.ShowDetectedDoor(new DoorPoseSolver.Solution{position=Vector3.zero,rotation=Quaternion.identity},.023f,.0558f), "camera candidate rejected");
            Require(marker.HasImageCandidate && !marker.IsEditing && !marker.IsBrowsing && portal.calibrationHidden,"amber candidate became confirmable placement");
            Call(marker,"HideMarks"); // Retarget when there is no live candidate; a visible candidate now freezes on explicit trigger.
            int revision = locator.hint.Revision; r.trigger = false; Send(); r.rotation = Quaternion.Euler(0, 175, 0); r.trigger = true; Send();
            Require(locator.hint.Revision != revision && !marker.IsEditing, "retarget recorded a manual corner");
            Require(!marker.HasImageCandidate && marker.IsGuiding, "retarget kept a stale image candidate or confirmed it");
            Call(marker, "OnApplicationFocus", false); Require(!marker.CanRunGuided, "camera can propose while unfocused");
            Call(marker, "OnApplicationFocus", true); r.trigger = false; Send();
            l.primary = true; Send(); l.primary = false; Send();
            Require(marker.IsEditing && !marker.IsGuiding && !locator.hint.Active, "X did not switch to manual");
            r.secondary = true; Send(); r.secondary = false; Send();
            Require(!marker.IsBrowsing && !marker.IsEditing && portal.calibrationHidden, "initial cancel exposed world");
            r.trigger = true; Send(); revision = locator.hint.Revision;
            r.secondary = true; Send(); r.secondary = false; Send();
            Set(locator, "_acquireRevision", revision); Set(locator, "_acquire", Task.FromResult(true)); Call(locator, "Update");
            Require(fake.calls == 0 && !marker.IsGuiding, "cancelled camera frame was consumed");
            r.trigger = false; Send(); r.trigger = true; Send();
            Require(marker.PreviewAutomaticPlacement(Vector3.zero, Quaternion.identity, .023f, .0558f), "guided preview rejected");
            // Simulate a new trigger edge coinciding with the camera proposal; it must not confirm.
            Set(marker, "_lastRight", new PortalControllerInput.Hand { tracked = true }); Send();
            Require(!marker.IsBrowsing && portal.calibrationHidden, "proposal accepted without a release");
            r.trigger = false; Send(); r.trigger = true; Send();
            Require(marker.IsBrowsing && !portal.calibrationHidden, "explicit confirmation failed");
            Vector3 confirmed = portal.portalPosition;
            r.trigger = false; Send(); r.trigger = true; Send(); Require(marker.IsGuiding && portal.calibrationHidden, "browse retarget failed");
            r.secondary = true; Send();
            Require(marker.IsBrowsing && !portal.calibrationHidden && portal.portalPosition == confirmed, "guided cancel did not restore previous view");
            foreach (string key in new[] { "compact_guided_search", "compact_guided_preview", "compact_guided_camera", "compact_guided_alignment", "footer_guided_flat" })
                Require(Resources.Load<Texture2D>("ControllerGuide/" + key) != null, "missing guide " + key);
        }
        finally
        {
            setter.Invoke(null, new object[] { ready }); DoorAutoLocator.Detector = previous;
            UnityEngine.Object.DestroyImmediate(locator.gameObject); UnityEngine.Object.DestroyImmediate(marker.gameObject);
        }
    }
    static int NetworkChecks()
    {
        string[] lines = File.ReadAllLines("../door-keypoint-model-20261118/unity_reference.txt");
        var detector = BarracudaDoorDetector.Create(WorkerFactory.Type.CSharpBurst); Require(detector != null, "network missing");
        var texture = new Texture2D(2, 2); var frame = new DoorCameraFrame(); var pixels = new Vector2[4]; var confidence = new float[4];
        int tested = 0, found = 0;
        try
        {
            for (int n = 1; n < lines.Length && tested < 12; n++)
            {
                string[] p = lines[n].Split(' '); if (p.Length < 19 || p[1] != "1" || p[2] != "1") continue;
                texture.LoadImage(File.ReadAllBytes(Path.Combine(lines[0], "images", p[0] + ".jpg")));
                var colors = texture.GetPixels32(); int w = texture.width, h = texture.height;
                frame.gray = new byte[w * h]; frame.width = w; frame.height = h; frame.time = ++tested * 100;
                for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { var c = colors[(h - y - 1) * w + x]; frame.gray[y * w + x] = (byte)((c.r * 77 + c.g * 150 + c.b * 29) >> 8); }
                Vector2 lo = new Vector2(float.PositiveInfinity, float.PositiveInfinity), hi = -lo;
                var labels = new Vector2[4];
                for (int k = 0; k < 4; k++) { labels[k] = new Vector2(float.Parse(p[11 + k * 2], CultureInfo.InvariantCulture), float.Parse(p[12 + k * 2], CultureInfo.InvariantCulture)); lo = Vector2.Min(lo, labels[k]); hi = Vector2.Max(hi, labels[k]); }
                float ch = Mathf.Min(Mathf.Max((hi.y - lo.y) * 2.5f, 72), h, w * .75f), cw = ch * 4 / 3;
                Vector2 centre = (lo + hi) * .5f; centre.x = Mathf.Clamp(centre.x, cw * .5f, w - cw * .5f); centre.y = Mathf.Clamp(centre.y, ch * .5f, h - ch * .5f);
                var crop = new Rect(centre.x - cw * .5f, centre.y - ch * .5f, cw, ch); detector.Reset();
                if (!detector.TryDetectGuided(frame, crop, pixels, confidence)) continue;
                float worst = 0; for (int k = 0; k < 4; k++) worst = Mathf.Max(worst, Vector2.Distance(pixels[k], labels[k]));
                Require(detector.LastPasses <= 3 && detector.LastSearchRegion == crop, "guided search budget/region violated");
                Require(worst < Mathf.Max(10f, (hi.y - lo.y) * .08f), "guided corner error " + worst); found++;
            }
        }
        finally { detector.Dispose(); UnityEngine.Object.DestroyImmediate(texture); }
        Require(tested == 12 && found >= 10, "guided synthetic detector regression " + found + "/" + tested);
        Debug.Log("[GuidedDoorTrialCheck] synthetic local-search detections=" + found + "/" + tested);
        return found;
    }
}
