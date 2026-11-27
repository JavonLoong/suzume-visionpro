using System.Collections;
using System.Threading.Tasks;
using UnityEngine;

// Controller direction -> local camera search -> multi-frame pose -> explicitly confirmed preview.
// The user still confirms with the trigger, which stores the spatial anchor exactly as the manual flow does.
public class DoorAutoLocator : MonoBehaviour
{
    public static DoorAutoLocator Instance { get; private set; }
    public readonly DoorSearchHint hint = new DoorSearchHint();
    public string GuideStatus { get; private set; } = "guided_search";
    int _acquireRevision, _misses;
    float _guidedAt, _lastFrameAt;
    string _diagnosticGate = "search";
    Rect _diagnosticCrop;
    void Awake() { Instance = this; }

    public bool BeginGuided(Ray ray)
    {
        if (!(Detector is IDoorGuidedDetector guided) || !hint.Set(ray)) return false;
        guided.Reset(); stabilizer.Reset(); _misses = 0;
        _guidedAt = _lastFrameAt = Time.unscaledTime; _next = 0; GuideStatus = "guided_search";
        _permissionAsked = false;
        // Permit an explicit retry after a camera startup failure, without opening two sessions.
        if (_start != null && _start.IsCompleted && (_camera == null || !_camera.IsRunning))
        { _camera?.Dispose(); _camera = null; _start = null; }
        Debug.Log($"[DoorAuto] guided target revision={hint.Revision} origin={ray.origin:F3} direction={ray.direction:F3}");
        return true;
    }
    public void CancelGuided()
    {
        hint.Clear(); stabilizer.Reset(); (Detector as IDoorGuidedDetector)?.Reset();
    }
    // The trained corner network by default; without one the camera is never opened and only the manual flow runs.
    public static IDoorKeypointDetector Detector;

    public float interval = .15f, minimumConfidence = .5f, minimumDoorPixels = 24f;
    // Off by default: on the 640x480 synthetic set it moved corners away from the labels
    // (median 1.17 -> 1.62 px). Re-measure on full-resolution headset images before enabling.
    public bool refineEdges = false;
    public bool refineCorners = true;
    public bool saveDiagnosticFrames = false;
    public int maximumSavedFrames = 30;
    public readonly DoorPoseStabilizer stabilizer = new DoorPoseStabilizer { assumeUpright=false };

    PicoDoorCamera _camera;
    DoorCornerRefiner _cornerRefiner;
    readonly float[] _cornerScores=new float[4];
    bool _refinementApplied,_refinementAttempted;
    Task<bool> _start, _acquire;
    readonly DoorCameraFrame _frame = new DoorCameraFrame();
    readonly Vector2[] _pixels = new Vector2[4], _refined = new Vector2[4];
    readonly float[] _confidence = new float[4];
    float _next;
    bool _permissionAsked, _gripWas, _trackedWas;
    float _nextDiagnostic;
    int _savedFrames;
    bool _cameraProbe;
    bool _processing;
    float _probeUntil;

    void Start()
    {
        if(Application.isEditor || Application.platform!=RuntimePlatform.Android) return;
        using(var player=new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using(var activity=player.GetStatic<AndroidJavaObject>("currentActivity"))
        using(var intent=activity.Call<AndroidJavaObject>("getIntent")) {
            _cameraProbe=intent.Call<bool>("getBooleanExtra","door_camera_probe",false);
            refineCorners=intent.Call<bool>("getBooleanExtra","door_corner_refinement",refineCorners);
            if(_cameraProbe) intent.Call("removeExtra","door_camera_probe");
        }
        if(refineCorners)_cornerRefiner=DoorCornerRefiner.Create();
        _probeUntil=Time.unscaledTime+20;
        if(_cameraProbe) Debug.Log("[DoorCamera] explicit ADB camera preflight requested; no automatic placement");
    }

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
            DoorPhysicalSize.Cycle(); stabilizer.Reset(); hint.RestartScales();
            (Detector as IDoorGuidedDetector)?.Reset();
            _guidedAt = Time.unscaledTime; _misses = 0;
            Debug.Log($"[DoorAuto] door size {DoorPhysicalSize.Name} {DoorPhysicalSize.Width:F4}x{DoorPhysicalSize.Height:F4}m");
            marker.Notice("door_size_" + DoorPhysicalSize.Index, 2f);
            StartCoroutine(Pulses(DoorPhysicalSize.Index + 1));
        }
        _gripWas = grip; _trackedWas = left.tracked;

        if (_processing || (Detector is BarracudaDoorDetector inFlight && inFlight.IsRunning)) return; // Own the frame buffer until inference and pose fitting finish.
        if (_acquire != null)
        {
            if (!_acquire.IsCompleted) return;
            bool fresh = !_acquire.IsFaulted && _acquire.Result;
            _acquire = null;
            if(fresh && _cameraProbe) {
                _cameraProbe=false;
                Debug.Log($"[DoorCamera] preflight PASS: received {_frame.width}x{_frame.height} camera frame");
            }
            if (fresh && _acquireRevision == hint.Revision && marker.CanRunGuided)
            { _lastFrameAt = Time.unscaledTime; _processing = true; StartCoroutine(ProcessAsync(marker, _acquireRevision)); return; }
        }
        if (!hint.Active || !marker.CanRunGuided || Detector == null) {
            if(_cameraProbe) ProbeCamera();
            return;
        }
        if (!EnsureCamera())
        {
            GuideStatus = _camera != null && !string.IsNullOrEmpty(_camera.Failure) ? "guided_camera" : "guided_permission";
            return;
        }
        if (Time.unscaledTime - _lastFrameAt > 6f) GuideStatus = "guided_camera";
        if (Camera.main == null || Time.unscaledTime < _next) return;
        _next = Time.unscaledTime + interval;
        var head = Camera.main.transform;
        Matrix4x4 headToWorld = Matrix4x4.TRS(head.position, head.rotation, Vector3.one);
        float time = Time.unscaledTime;
        _acquireRevision = hint.Revision;
        var sample = _camera.SamplePose(headToWorld, time);
        _acquire = Task.Run(() => _camera.TryAcquire(sample, _frame));
    }

    void ProbeCamera()
    {
        if(Time.unscaledTime>_probeUntil || (_camera!=null && !string.IsNullOrEmpty(_camera.Failure))) {
            _cameraProbe=false;
            Debug.LogWarning("[DoorCamera] preflight FAILED: "+(_camera?.Failure ?? "no frame before timeout"));
            return;
        }
        if(!EnsureCamera() || Camera.main==null || Time.unscaledTime<_next) return;
        _next=Time.unscaledTime+interval;
        var head=Camera.main.transform;
        Matrix4x4 pose=Matrix4x4.TRS(head.position,head.rotation,Vector3.one);
        float time=Time.unscaledTime;
        _acquireRevision=hint.Revision;
        var sample=_camera.SamplePose(pose,time);
        _acquire=Task.Run(()=>_camera.TryAcquire(sample,_frame));
    }

    IEnumerator ProcessAsync(DoorCornerMarker marker, int revision)
    {
        try { yield return ProcessFrame(marker, revision); }
        finally { _processing = false; }
    }

    IEnumerator ProcessFrame(DoorCornerMarker marker, int revision)
    {
        _refinementApplied=_refinementAttempted=false;
        System.Array.Clear(_cornerScores,0,4);
        if (!marker.CanRunGuided || !hint.Active || !(Detector is IDoorGuidedDetector guided)) yield break;
        if (!hint.TryCrop(_frame, DoorPhysicalSize.Height, out var crop))
        { GuideStatus = "guided_offscreen"; stabilizer.MarkMissing(_frame.time); yield break; }
        var watch = System.Diagnostics.Stopwatch.StartNew();
        _diagnosticCrop = crop;
        bool found = false;
        bool Valid() => revision == hint.Revision && marker != null && marker.CanRunGuided && hint.Active
            && Time.unscaledTime - _frame.time <= 1f;
        if (guided is BarracudaDoorDetector network)
            yield return network.DetectGuidedAsync(_frame, crop, _pixels, _confidence, result => found = result, Valid);
        else found = guided.TryDetectGuided(_frame, crop, _pixels, _confidence);
        if (!Valid()) yield break;
        // Old results must not pull the outline behind a moving head.
        if (Time.unscaledTime - _frame.time > 1f) { GuideStatus = "guided_search"; yield break; }
        bool usable = found && Plausible();
        if (!usable) { watch.Stop(); _diagnosticGate=found ? "corner_quality" : "not_detected"; Missing(); Diagnose(found,usable,(float)watch.Elapsed.TotalMilliseconds); yield break; }
        if(refineCorners&&_cornerRefiner!=null)
        {
            bool accepted=false;
            _refinementAttempted=true;
            yield return _cornerRefiner.RefineAsync(_frame,_pixels,_refined,_cornerScores,result=>accepted=result,Valid);
            if(!Valid())yield break;
            if(accepted&&Mathf.Min(Vector2.Distance(_refined[0],_refined[2]),Vector2.Distance(_refined[1],_refined[3]))>=minimumDoorPixels)
            {_refined.CopyTo(_pixels,0);_refinementApplied=true;}
        }
        watch.Stop();
        if (refineEdges && DoorEdgeRefiner.Refine(_frame.gray, _frame.width, _frame.height, _pixels, _refined) > 0)
            _refined.CopyTo(_pixels, 0);
        var observation = new DoorPoseSolver.Observation
        { cameraToWorld = _frame.cameraToWorld, fx = _frame.fx, fy = _frame.fy, cx = _frame.cx, cy = _frame.cy, time = _frame.time };
        observation.SetPixels(_pixels);
        float physicalWidth=DoorPhysicalSize.Width, physicalHeight=DoorPhysicalSize.Height;
        var solve=Task.Run(()=> { bool ok=DoorPoseSolver.SolveSingle(observation,physicalWidth,physicalHeight,out var pose);return (ok,pose); });
        while(!solve.IsCompleted)yield return null;
        if(!Valid())yield break;
        var single=solve.IsFaulted?default:solve.Result.pose;
        if (solve.IsFaulted || !solve.Result.ok)
        { _diagnosticGate="pose_fit"; guided.Reset(); Missing(); Diagnose(found,usable,(float)watch.Elapsed.TotalMilliseconds); yield break; }
        if (!hint.Accepts(single.position + single.rotation * Vector3.up * (DoorPhysicalSize.Height * .5f), DoorPhysicalSize.Height))
        { _diagnosticGate="off_target"; guided.Reset(); Missing(); Diagnose(found,usable,(float)watch.Elapsed.TotalMilliseconds); yield break; }
        marker.ShowDetectedDoor(single,DoorPhysicalSize.Width,DoorPhysicalSize.Height);
        _misses = 0; GuideStatus = "guided_stabilizing";
        hint.Focus(single.position + single.rotation * Vector3.up * (DoorPhysicalSize.Height * .5f));
        // The network's corner error grows with the door's size in the image (about 1 % of its height).
        float doorPixels = Mathf.Max(Vector2.Distance(_pixels[0], _pixels[2]), Vector2.Distance(_pixels[1], _pixels[3]));
        var proposal=stabilizer.Snapshot();proposal.maximumRmsPixels=Mathf.Max(1.5f,.02f*doorPixels);
        var stabilize=Task.Run(()=>proposal.Add(observation,physicalWidth,physicalHeight));
        while(!stabilize.IsCompleted)yield return null;
        if(!Valid())yield break;
        if(stabilize.IsFaulted){Missing();yield break;}
        stabilizer.CopyFrom(proposal);var change=stabilize.Result;
        _diagnosticGate=stabilizer.Current.rmsPixels > stabilizer.maximumRmsPixels ? "alignment" : "stabilizing";
        if (_diagnosticGate=="alignment") GuideStatus="guided_alignment";
        Diagnose(found,usable,(float)watch.Elapsed.TotalMilliseconds);
        if (change == DoorPoseStabilizer.Event.None) yield break;
        var pose = change == DoorPoseStabilizer.Event.Locked ? stabilizer.LockedSolution : stabilizer.Current;
        Debug.Log($"[DoorAuto] {change} position={pose.position:F4} yaw={pose.yawDegrees:F1} rms={pose.rmsPixels:F2}px views={stabilizer.ObservationCount}");
        if (change == DoorPoseStabilizer.Event.Locked
            && hint.Accepts(pose.position + pose.rotation * Vector3.up * (DoorPhysicalSize.Height * .5f), DoorPhysicalSize.Height))
            marker.PreviewAutomaticPlacement(pose.position, pose.rotation, DoorPhysicalSize.Width, DoorPhysicalSize.Height);
    }

    void Missing()
    {
        stabilizer.MarkMissing(_frame.time);
        if (++_misses >= 3) { hint.ClearFocus(); (Detector as IDoorGuidedDetector)?.Reset(); }
        GuideStatus = Time.unscaledTime - _guidedAt > 6f ? "guided_retry" : "guided_search";
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
        line += $"\nlocalCorners attempted={_refinementAttempted} applied={_refinementApplied} ms={(_refinementAttempted?_cornerRefiner.LastMilliseconds:0):F1} sliceMs={(_refinementAttempted?_cornerRefiner.MaximumSliceMilliseconds:0):F2} scores={_cornerScores[0]:F3},{_cornerScores[1]:F3},{_cornerScores[2]:F3},{_cornerScores[3]:F3}";
        line += $"\ncapturePose {_frame.poseCorrected} ageMs {_frame.captureAge*1000:F1}\ngate {_diagnosticGate} crop {_diagnosticCrop} poseRms {stabilizer.Current.rmsPixels:F2} observations {stabilizer.ObservationCount}";
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
        foreach (float c in _confidence) if (float.IsNaN(c) || float.IsInfinity(c) || c < minimumConfidence) return false;
        foreach (var p in _pixels)
            if (float.IsNaN(p.x + p.y) || float.IsInfinity(p.x + p.y)
                || p.x < 0 || p.y < 0 || p.x >= _frame.width || p.y >= _frame.height) return false;
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

    void OnDestroy() { if (Instance == this) Instance = null; _camera?.Dispose(); _cornerRefiner?.Dispose(); }
}
