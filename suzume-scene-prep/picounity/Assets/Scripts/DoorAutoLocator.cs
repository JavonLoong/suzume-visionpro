using System.Collections;
using System.Threading.Tasks;
using UnityEngine;

// Camera frame -> detector -> edge refinement -> multi-frame pose -> preview on the existing door flow.
// The user still confirms with the trigger, which stores the spatial anchor exactly as the manual flow does.
public class DoorAutoLocator : MonoBehaviour
{
    // The trained corner network by default; without one the camera is never opened and only the manual flow runs.
    public static IDoorKeypointDetector Detector;

    public float interval = .15f, minimumConfidence = .5f, minimumDoorPixels = 24f, retryAfterCancel = 5f;
    // Off by default: on the 640x480 synthetic set it moved corners away from the labels
    // (median 1.17 -> 1.62 px). Re-measure on full-resolution headset images before enabling.
    public bool refineEdges = false;
    public bool saveDiagnosticFrames = true;
    public int maximumSavedFrames = 30;
    public readonly DoorPoseStabilizer stabilizer = new DoorPoseStabilizer();

    PicoDoorCamera _camera;
    Task<bool> _start, _acquire;
    readonly DoorCameraFrame _frame = new DoorCameraFrame();
    readonly Vector2[] _pixels = new Vector2[4], _refined = new Vector2[4];
    readonly float[] _confidence = new float[4];
    float _next, _proposed = float.NegativeInfinity;
    bool _permissionAsked, _gripWas, _trackedWas;
    float _nextDiagnostic;
    int _savedFrames;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if (Application.isEditor || Application.platform != RuntimePlatform.Android) return;
        if (Detector == null) Detector = BarracudaDoorDetector.Create();
        new GameObject("DoorAutoLocator").AddComponent<DoorAutoLocator>();
    }

    void Update()
    {
        var marker = DoorCornerMarker.Instance;
        if (marker == null) return;
        var left = PortalControllerInput.Read(false);
        bool grip = left.tracked && left.grip;
        // Left grip before placement: next door size preset; the number of pulses tells which one.
        if (grip && !_gripWas && _trackedWas && !marker.IsEditing && !marker.IsBrowsing && !marker.IsBusy)
        {
            DoorPhysicalSize.Cycle(); stabilizer.Reset();
            Debug.Log($"[DoorAuto] door size {DoorPhysicalSize.Name} {DoorPhysicalSize.Width:F4}x{DoorPhysicalSize.Height:F4}m");
            StartCoroutine(Pulses(DoorPhysicalSize.Index + 1));
        }
        _gripWas = grip; _trackedWas = left.tracked;

        if (Detector == null || !EnsureCamera()) return;
        if (_acquire != null)
        {
            if (!_acquire.IsCompleted) return;
            bool fresh = !_acquire.IsFaulted && _acquire.Result;
            _acquire = null;
            if (fresh) Process(marker);
        }
        if (marker.IsBusy || marker.IsEditing || Camera.main == null || Time.unscaledTime < _next) return;
        // A cancelled proposal is not repeated at once; the user may want the manual flow.
        if (stabilizer.CurrentState == DoorPoseStabilizer.State.Locked && !marker.IsBrowsing)
        {
            if (Time.unscaledTime - _proposed < retryAfterCancel) return;
            stabilizer.Reset();
        }
        _next = Time.unscaledTime + interval;
        var head = Camera.main.transform;
        Matrix4x4 headToWorld = Matrix4x4.TRS(head.position, head.rotation, Vector3.one);
        float time = Time.unscaledTime;
        _acquire = Task.Run(() => _camera.TryAcquire(headToWorld, time, _frame));
    }

    void Process(DoorCornerMarker marker)
    {
        if (marker.IsBusy || marker.IsEditing) return;
        var watch = System.Diagnostics.Stopwatch.StartNew();
        bool found = Detector.TryDetect(_frame, _pixels, _confidence);
        watch.Stop();
        bool usable = found && Plausible();
        Diagnose(found, usable, (float)watch.Elapsed.TotalMilliseconds);
        if (!usable) { stabilizer.MarkMissing(_frame.time); return; }
        if (refineEdges && DoorEdgeRefiner.Refine(_frame.gray, _frame.width, _frame.height, _pixels, _refined) > 0)
            _refined.CopyTo(_pixels, 0);
        var observation = new DoorPoseSolver.Observation
        { cameraToWorld = _frame.cameraToWorld, fx = _frame.fx, fy = _frame.fy, cx = _frame.cx, cy = _frame.cy, time = _frame.time };
        observation.SetPixels(_pixels);
        // The network's corner error grows with the door's size in the image (about 1 % of its height).
        float doorPixels = Mathf.Max(Vector2.Distance(_pixels[0], _pixels[2]), Vector2.Distance(_pixels[1], _pixels[3]));
        stabilizer.maximumRmsPixels = Mathf.Max(1.5f, .02f * doorPixels);
        var change = stabilizer.Add(observation, DoorPhysicalSize.Width, DoorPhysicalSize.Height);
        if (change == DoorPoseStabilizer.Event.None) return;
        var pose = change == DoorPoseStabilizer.Event.Locked ? stabilizer.LockedSolution : stabilizer.Current;
        Debug.Log($"[DoorAuto] {change} position={pose.position:F4} yaw={pose.yawDegrees:F1} rms={pose.rmsPixels:F2}px views={stabilizer.ObservationCount}");
        if (change == DoorPoseStabilizer.Event.Locked
            && marker.PreviewAutomaticPlacement(pose.position, pose.rotation, DoorPhysicalSize.Width, DoorPhysicalSize.Height))
            _proposed = Time.unscaledTime;
    }

    // Log line every two seconds and, for the first frames, the camera image itself with everything
    // needed to re-run the pose maths on a PC: <persistentDataPath>/doorcam/NNN.pgm + NNN.txt.
    void Diagnose(bool found, bool usable, float milliseconds)
    {
        if (_frame.time < _nextDiagnostic) return;
        _nextDiagnostic = _frame.time + 2f;
        string line = string.Format(System.Globalization.CultureInfo.InvariantCulture,
            "size {0} {1}\nintrinsics {2} {3} {4} {5}\nfound {6} usable {7} state {8} ms {9:F1}\nconfidence {10:F3} {11:F3} {12:F3} {13:F3}\npixels {14:F2} {15:F2} {16:F2} {17:F2} {18:F2} {19:F2} {20:F2} {21:F2}\ndoor {22} {23}\ncameraToWorld",
            _frame.width, _frame.height, _frame.fx, _frame.fy, _frame.cx, _frame.cy, found ? 1 : 0, usable ? 1 : 0, stabilizer.CurrentState, milliseconds,
            _confidence[0], _confidence[1], _confidence[2], _confidence[3],
            _pixels[0].x, _pixels[0].y, _pixels[1].x, _pixels[1].y, _pixels[2].x, _pixels[2].y, _pixels[3].x, _pixels[3].y,
            DoorPhysicalSize.Width, DoorPhysicalSize.Height);
        for (int i = 0; i < 16; i++) line += " " + _frame.cameraToWorld[i / 4, i % 4].ToString("R", System.Globalization.CultureInfo.InvariantCulture);
        Debug.Log("[DoorAuto] frame " + line.Replace('\n', ';'));
        if (!saveDiagnosticFrames || _savedFrames >= maximumSavedFrames) return;
        try
        {
            string folder = System.IO.Path.Combine(Application.persistentDataPath, "doorcam");
            if (_savedFrames == 0)
            {
                if (System.IO.Directory.Exists(folder)) System.IO.Directory.Delete(folder, true);
                System.IO.Directory.CreateDirectory(folder);
            }
            string name = System.IO.Path.Combine(folder, _savedFrames.ToString("000"));
            byte[] header = System.Text.Encoding.ASCII.GetBytes($"P5\n{_frame.width} {_frame.height}\n255\n");
            var file = new byte[header.Length + _frame.width * _frame.height];
            System.Buffer.BlockCopy(header, 0, file, 0, header.Length);
            System.Buffer.BlockCopy(_frame.gray, 0, file, header.Length, _frame.width * _frame.height);
            _savedFrames++;
            Task.Run(() => { System.IO.File.WriteAllBytes(name + ".pgm", file); System.IO.File.WriteAllText(name + ".txt", line); });
        }
        catch (System.Exception e) { Debug.LogWarning("[DoorAuto] cannot save frame: " + e.Message); _savedFrames = maximumSavedFrames; }
    }

    bool Plausible()
    {
        foreach (float c in _confidence) if (c < minimumConfidence) return false;
        Vector2 bl = _pixels[0], br = _pixels[1], tl = _pixels[2], tr = _pixels[3];
        if (Mathf.Min(Vector2.Distance(bl, tl), Vector2.Distance(br, tr)) < minimumDoorPixels) return false;
        // Convex and consistently wound: walking BL, BR, TR, TL must always turn the same way.
        Vector2[] ring = { bl, br, tr, tl };
        float sign = 0;
        for (int i = 0; i < 4; i++)
        {
            Vector2 a = ring[(i + 1) % 4] - ring[i], b = ring[(i + 2) % 4] - ring[(i + 1) % 4];
            float cross = a.x * b.y - a.y * b.x;
            if (Mathf.Abs(cross) < 1e-3f || (sign != 0 && cross * sign < 0)) return false;
            sign = cross;
        }
        return true;
    }

    bool EnsureCamera()
    {
        if (_camera != null && _camera.IsRunning) return true;
        if (_start != null) return false; // starting, or failed once: the manual flow stays available
        if (!PicoDoorCamera.HasPermission)
        {
            if (!_permissionAsked) { _permissionAsked = true; PicoDoorCamera.RequestPermission(); }
            return false;
        }
        _camera = new PicoDoorCamera();
        _start = _camera.StartAsync();
        return false;
    }

    IEnumerator Pulses(int count)
    {
        for (int i = 0; i < count; i++) { PortalControllerInput.Pulse(false); yield return new WaitForSecondsRealtime(.22f); }
    }

    void OnDestroy() { _camera?.Dispose(); }
}
