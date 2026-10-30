using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Unity.XR.PXR;
using UnityEngine;

// Each corner is located by two controller rays from different positions.
public class DoorCornerMarker : MonoBehaviour
{
    const string PlacementKey = "SuzumePortal.DoorPlacement.V3";
    enum Mode { Ready, Collect, Preview, Browse }
    [Serializable] class SavedPlacement { public string uuid; public float width, height; }
    struct PreviousPlacement
    {
        public Vector3 position; public float yaw, width, height;
        public PortalConfig.FrameMode frame; public bool leaf, fullView;
    }
    public static DoorCornerMarker Instance { get; private set; }
    public bool IsEditing => _mode == Mode.Collect || _mode == Mode.Preview;
    public bool IsBrowsing => _mode == Mode.Browse;
    public bool IsBusy => _busy;
    public string ProgressSummary => $"mode={_mode} corners={_count} firstRay={_hasFirstRay}";
    bool _paused, _focused = true;
    PortalManager _portal;
    Mode _mode;
    PreviousPlacement _previous;
    DoorCalibrationMath.Placement _fit;
    readonly Vector3[] _corners = new Vector3[4];
    readonly Transform[] _marks = new Transform[4];
    PortalControllerInput.Hand _lastRight, _lastLeft;
    PortalGuideView _guide;
    Transform _tip;
    Transform _firstNearest, _secondNearest;
    LineRenderer _outline;
    LineRenderer _laser;
    LineRenderer _firstLine;
    LineRenderer _nearestBridge;
    readonly Ray[] _firstRays = new Ray[4];
    Ray _firstRay, _displayRay;
    bool _hasFirstRay, _rayHit, _rayFresh, _hasDisplayRay;
    DoorRayIntersection.Solution _solution;
    string _rayProblem;
    Material _material;
    int _count;
    bool _busy, _providerReady, _persistent, _help = true;
    bool _previousWasBrowse, _selectedMountain;
    Task _prepareTask;
    ulong _anchor;
    SavedPlacement _saved;
    string _status = "intro", _notice;
    float _noticeUntil, _nextLocate;
    readonly CancellationTokenSource _lifetime = new CancellationTokenSource();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if (!Application.isEditor && Application.platform == RuntimePlatform.Android)
            new GameObject("DoorCornerMarker").AddComponent<DoorCornerMarker>();
    }
    void Start()
    {
        Instance = this;
        _portal = FindObjectOfType<PortalManager>();
        _selectedMountain=_portal.mountainLandscape;
        _portal.calibrationHidden=true;
        _portal.UpdatePortalState();
        _material = Resources.Load<Material>("DoorMark/MarkLabel");
        _tip = Sphere("TwoRayIntersection", new Color(.3f,1f,.6f), .025f);
        _firstNearest=Sphere("NearestPointOnFirstRay",new Color(.3f,.65f,1f),.015f);
        _secondNearest=Sphere("NearestPointOnSecondRay",new Color(1f,.65f,.2f),.015f);
        _nearestBridge=new GameObject("ClosestPointBridge").AddComponent<LineRenderer>();
        _nearestBridge.transform.SetParent(transform,false);_nearestBridge.useWorldSpace=true;_nearestBridge.positionCount=2;
        _nearestBridge.sharedMaterial=new Material(_material);_nearestBridge.startWidth=_nearestBridge.endWidth=.004f;
        _nearestBridge.enabled=false;
        _laser=new GameObject("ControllerAimRay").AddComponent<LineRenderer>();
        _laser.transform.SetParent(transform,false);_laser.useWorldSpace=true;_laser.positionCount=2;
        _laser.sharedMaterial=new Material(_material);_laser.startWidth=.0025f;_laser.endWidth=.0035f;
        _laser.enabled=false;
        _firstLine=new GameObject("FirstRecordedRay").AddComponent<LineRenderer>();
        _firstLine.transform.SetParent(transform,false);_firstLine.useWorldSpace=true;_firstLine.positionCount=2;
        _firstLine.sharedMaterial=new Material(_material);_firstLine.sharedMaterial.color=new Color(.3f,.65f,1f,.8f);
        _firstLine.startWidth=_firstLine.endWidth=.003f;_firstLine.enabled=false;
        Color[] colors = { Color.yellow, Color.cyan, Color.green, new Color(1f,.4f,.7f) };
        for (int i = 0; i < 4; i++) { _marks[i] = Sphere("Corner" + i, colors[i], .025f); _marks[i].gameObject.SetActive(false); }
        _outline = new GameObject("DoorOutline").AddComponent<LineRenderer>();
        _outline.transform.SetParent(transform, false);
        _outline.material = new Material(_material); _outline.material.color = new Color(.3f,1f,.6f);
        _outline.startWidth = _outline.endWidth = .006f; _outline.positionCount = 5; _outline.enabled = false;
        _guide = new GameObject("PortalGuide").AddComponent<PortalGuideView>();
        if (Camera.main != null) _guide.Initialize(Camera.main);
        _prepareTask = Prepare();
    }
    void Update()
    {
        if (_portal == null) return;
        ProcessInput(PortalControllerInput.Read(true),PortalControllerInput.Read(false));
    }
    void ProcessInput(PortalControllerInput.Hand right,PortalControllerInput.Hand left)
    {
        // Preserve the selected corners/ray across sleep or a system dialog.
        if (_paused || !_focused) { _rayFresh=false; return; }
        UpdateRay(right);
        if (!_busy)
        {
            if (Rise(right.primary, _lastRight.primary, right.tracked, _lastRight.tracked))
            {
                _selectedMountain=!_selectedMountain;
                // During placement, choose the next landscape without rebuilding geometry
                // or replacing the current step. It becomes visible only on confirmation.
                if(IsBrowsing) { _portal.SetLandscape(_selectedMountain);Notice(_selectedMountain ? "mountain" : "flat", 2f); }
                PortalControllerInput.Pulse(true);
            }
            if (Rise(left.primary, _lastLeft.primary, left.tracked, _lastLeft.tracked)) Begin();
            if (Rise(right.secondary, _lastRight.secondary, right.tracked, _lastRight.tracked))
            {
                if (IsEditing) Cancel(); else _help = !_help;
            }
            if (Rise(left.secondary, _lastLeft.secondary, left.tracked, _lastLeft.tracked) && !IsEditing)
            {
                if(_mode==Mode.Ready) RestoreSaved();
                else
                {
                    _portal.frameMode = _portal.frameMode == PortalConfig.FrameMode.Reference ? PortalConfig.FrameMode.Occlusion : PortalConfig.FrameMode.Reference;
                    _portal.UpdatePortalState();
                    Notice(_portal.frameMode == PortalConfig.FrameMode.Reference ? "frame_on" : "frame_off", 2f);
                }
            }
            if (IsEditing && Rise(left.trigger, _lastLeft.trigger, left.tracked, _lastLeft.tracked)) Undo();
            else if (!IsBrowsing && PicoPassthroughSetup.IsReady && Rise(right.trigger, _lastRight.trigger, right.tracked, _lastRight.tracked))
            {
                if(_mode==Mode.Ready) Begin();
                if (_mode == Mode.Preview) _ = Confirm();
                else if (_count < 4)
                {
                    if(!_hasFirstRay)
                    {
                        _firstRay=PortalControllerInput.AimRay(right);_hasFirstRay=true;_rayHit=false;_noticeUntil=0;
                        PortalControllerInput.Pulse(true);
                        Debug.Log($"[PortalRay] corner={_count+1} first ray recorded origin={_firstRay.origin:F3}");
                    }
                    else if(_rayFresh)
                    {
                        Debug.Log($"[PortalRay] corner={_count+1} second ray gap={_solution.gap:F3}m angle={_solution.angle:F1} distance={_solution.secondDistance:F2}m point={_solution.point:F3}");
                        Add(_solution.point);
                    }
                    else Notice(_rayProblem??"ray_baseline",2f);
                }
            }
        }
        _lastRight = right; _lastLeft = left;
        UpdateRay(right);
        if (IsBrowsing && !_busy && _anchor != 0 && Time.unscaledTime >= _nextLocate)
        {
            _nextLocate = Time.unscaledTime + .1f;
            if (PXR_MixedReality.LocateAnchor(_anchor, out var pos, out var rot) == PxrResult.SUCCESS)
            {
                Apply(PortalControllerInput.ToWorld(pos), PortalControllerInput.ToWorld(rot), _saved.width, _saved.height);
                _status = "saved";
            }
            else _status = "locating";
        }
        string status = !IsBrowsing && !PicoPassthroughSetup.IsReady ? "passthrough_wait" : (_busy ? "busy" : (!IsBrowsing && !right.tracked ? "wait" : CurrentStatus()));
        _guide?.Show(status, _help || !IsBrowsing || _busy || (_noticeUntil > Time.unscaledTime), _selectedMountain,
            _mode==Mode.Ready ? PortalGuideView.Context.Ready : (IsBrowsing ? PortalGuideView.Context.Browse : PortalGuideView.Context.Placement));
        _guide?.ShowRayGap(_solution.gap,_mode==Mode.Collect && _hasFirstRay && _rayHit);
    }
    void UpdateRay(PortalControllerInput.Hand hand)
    {
        bool active=(_mode==Mode.Ready || _mode==Mode.Collect) && _count<4 && !_busy;
        _rayFresh=false;
        if(!_hasFirstRay) _rayHit=false;
        _firstLine.enabled=_mode==Mode.Collect && _count<4 && _hasFirstRay;
        if(active && hand.tracked && PicoPassthroughSetup.IsReady)
        {
            Ray ray=PortalControllerInput.AimRay(hand);
            if(_hasFirstRay)
            {
                _rayFresh=DoorRayIntersection.TrySolve(_firstRay,ray,out var next,out _rayProblem,_rayHit ? _solution.firstDistance : 2f);
                if(_rayFresh) { _solution=next;_rayHit=true;_displayRay=ray;_hasDisplayRay=true; }
            }
            else { _displayRay=ray;_hasDisplayRay=true; }
        }
        _laser.enabled=active&&_hasDisplayRay;
        if(_laser.enabled)
        {
            _laser.SetPosition(0,_displayRay.origin);
            _laser.SetPosition(1,_displayRay.GetPoint(_rayHit ? Mathf.Max(.3f,_solution.secondDistance) : DoorRayIntersection.MaximumDistance));
            Color feedback=hand.tracked ? new Color(.3f,1f,.6f) : new Color(.65f,.7f,.75f);
            _laser.sharedMaterial.color=feedback;
            if(_rayHit)
            {
                _tip.position=_solution.point;_tip.localScale=Vector3.one*Mathf.Clamp(_solution.secondDistance*.012f,.025f,1f);
                _tip.GetComponent<Renderer>().sharedMaterial.color=feedback;
                _firstNearest.position=_solution.firstPoint;_secondNearest.position=_solution.secondPoint;
                _nearestBridge.SetPositions(new[]{_solution.firstPoint,_solution.secondPoint});_nearestBridge.sharedMaterial.color=feedback;
            }
        }
        if(_firstLine.enabled)
        {
            _firstLine.SetPosition(0,_firstRay.origin);
            _firstLine.SetPosition(1,_firstRay.GetPoint(_rayHit ? Mathf.Max(.3f,_solution.firstDistance) : DoorRayIntersection.MaximumDistance));
        }
        _tip.gameObject.SetActive(active&&_rayHit);
        _firstNearest.gameObject.SetActive(active&&_rayHit);_secondNearest.gameObject.SetActive(active&&_rayHit);
        _nearestBridge.enabled=active&&_rayHit;
    }
    static bool Rise(bool now, bool was, bool tracked, bool wasTracked) => tracked && wasTracked && now && !was;
    string CurrentStatus()
    {
        if (_noticeUntil > Time.unscaledTime) return _notice;
        if (_mode == Mode.Ready) return "ready";
        if (_mode == Mode.Collect && _hasFirstRay && _rayHit)
        {
            if (_solution.parallel) return "ray_parallel";
            if (_solution.firstDistance > DoorRayIntersection.MaximumDistance || _solution.secondDistance > DoorRayIntersection.MaximumDistance) return "ray_far";
            if (_solution.firstDistance < .1f || _solution.secondDistance < .1f) return "ray_origin";
        }
        if (_mode == Mode.Collect && _count < 4) return (_hasFirstRay ? "pair" : "step") + _count;
        return _status;
    }
    public void Notice(string label, float seconds = 3f) { _notice = label; _noticeUntil = Time.unscaledTime + seconds; }
    void Begin()
    {
        if (!IsEditing)
        {
            _previousWasBrowse=IsBrowsing;
            _previous = new PreviousPlacement { position = _portal.portalPosition, yaw = _portal.portalYaw, width = _portal.portalWidth, height = _portal.portalHeight, frame = _portal.frameMode, leaf = _portal.showDoorLeaf, fullView = _portal.fullMeadowView };
        }
        _mode = Mode.Collect; _count = 0; _help = true; _noticeUntil = 0;_hasFirstRay=false;_rayHit=false;_hasDisplayRay=false;
        _portal.calibrationHidden = true; _portal.fullMeadowView = false;
        _portal.UpdatePortalState();
        PicoPassthroughSetup.RequestEnable();
        _outline.enabled = false;
        foreach (var mark in _marks) mark.gameObject.SetActive(false);
        Debug.Log("[DoorCorner] four-corner calibration started; two rays per corner");
    }
    void Add(Vector3 point)
    {
        for (int i = 0; i < _count; i++)
            if (Vector3.Distance(point, _corners[i]) < .08f) { Notice("error_duplicate"); return; }
        _firstRays[_count]=_firstRay;_hasFirstRay=false;_noticeUntil=0;
        _corners[_count] = point; _marks[_count].position = point; _marks[_count].gameObject.SetActive(true); _count++;
        PortalControllerInput.Pulse(true);
        Debug.Log("[DoorCorner] captured " + _count + " " + point.ToString("F3"));
        if (_count != 4) return;
        if (!DoorCalibrationMath.TryFit(_corners, Camera.main.transform.position, out _fit, out string error))
        {
            _status = error; _noticeUntil = 0; return;
        }
        _mode = Mode.Preview; _status = "preview"; _noticeUntil = 0;
        // Preview only the thin outline over the physical door, until explicit confirmation.
        _portal.calibrationHidden = true;
        Apply(_fit.center, _fit.rotation, _fit.width, _fit.height);
        _outline.SetPositions(new[] { _corners[0], _corners[1], _corners[3], _corners[2], _corners[0] });
        _outline.enabled = true;
        Debug.Log($"[DoorCorner] preview width={_fit.width:F3} height={_fit.height:F3}");
    }
    void Undo()
    {
        if(_hasFirstRay) { _hasFirstRay=false;_rayHit=false;_noticeUntil=0;PortalControllerInput.Pulse(false);return; }
        if (_count == 0) return;
        _count--; _marks[_count].gameObject.SetActive(false); _mode = Mode.Collect; _noticeUntil = 0;
        _firstRay=_firstRays[_count];_hasFirstRay=true;_rayHit=false;
        _portal.calibrationHidden = true; _outline.enabled = false; PortalControllerInput.Pulse(false);
        _portal.UpdatePortalState();
    }
    void Cancel()
    {
        _mode = _previousWasBrowse ? Mode.Browse : Mode.Ready;
        _portal.calibrationHidden = !IsBrowsing;_hasFirstRay=false;_rayHit=false;_hasDisplayRay=false;_count=0;
        if(IsBrowsing) _selectedMountain=_portal.mountainLandscape;
        _portal.frameMode = _previous.frame; _portal.showDoorLeaf = _previous.leaf; _portal.fullMeadowView = _previous.fullView;
        Apply(_previous.position, Quaternion.Euler(0,_previous.yaw,0), _previous.width, _previous.height);
        HideMarks(); _status = _persistent ? "saved" : "intro"; Notice(IsBrowsing ? "cancelled" : "ready");
    }
    void RestoreSaved()
    {
        if(_anchor==0 || _saved==null) { Notice("no_saved");return; }
        if(PXR_MixedReality.LocateAnchor(_anchor,out var position,out var rotation)!=PxrResult.SUCCESS) { Notice("locating");return; }
        _portal.SetLandscape(_selectedMountain);
        _portal.fullMeadowView=false;_portal.calibrationHidden=false;_mode=Mode.Browse;
        Apply(PortalControllerInput.ToWorld(position),PortalControllerInput.ToWorld(rotation),_saved.width,_saved.height);
        _status="saved";_noticeUntil=0;
        Debug.Log("[DoorCorner] explicitly restored saved placement");
    }
    void Apply(Vector3 center, Quaternion rotation, float width, float height)
    {
        _portal.portalPosition = center; _portal.portalYaw = rotation.eulerAngles.y;
        _portal.portalWidth = width; _portal.portalHeight = height; _portal.UpdatePortalState();
    }
    async Task Confirm()
    {
        _busy = true;
        ulong fresh = 0, previousHandle = 0;
        try
        {
            if(_prepareTask!=null) await _prepareTask;
            _persistent=false;previousHandle=_anchor;
            if (!_providerReady) throw new InvalidOperationException("spatial anchor provider unavailable");
            using (var timeout = CancellationTokenSource.CreateLinkedTokenSource(_lifetime.Token))
            {
                timeout.CancelAfter(10000);
                var create = await PXR_MixedReality.CreateSpatialAnchorAsync(PortalControllerInput.ToTracking(_fit.center), PortalControllerInput.ToTracking(_fit.rotation), timeout.Token);
                fresh = create.anchorHandle;
                if (create.result != PxrResult.SUCCESS) throw new InvalidOperationException("create " + create.result);
                var persist = await PXR_MixedReality.PersistSpatialAnchorAsync(fresh, timeout.Token);
                if (persist != PxrResult.SUCCESS) throw new InvalidOperationException("persist " + persist);
                if (this == null) return;
                _saved = new SavedPlacement { uuid = create.uuid.ToString(), width = _fit.width, height = _fit.height };
                PlayerPrefs.SetString(PlacementKey, JsonUtility.ToJson(_saved)); PlayerPrefs.Save();
                _anchor = fresh; fresh = 0; _persistent = true;
                Debug.Log("[DoorCorner] saved persistent door " + _saved.uuid);
                if (previousHandle != 0)
                {
                    try { await PXR_MixedReality.UnPersistSpatialAnchorAsync(previousHandle, timeout.Token); }
                    catch (Exception e) { Debug.LogWarning("[DoorCorner] old anchor cleanup " + e.Message); }
                    PXR_MixedReality.DestroyAnchor(previousHandle); previousHandle = 0;
                }
            }
        }
        catch (Exception e) { Debug.LogWarning("[DoorCorner] current-session placement only: " + e.Message); }
        finally
        {
            if (fresh != 0) PXR_MixedReality.DestroyAnchor(fresh);
            if (this != null)
            {
                if (!_persistent) { if (previousHandle != 0) PXR_MixedReality.DestroyAnchor(previousHandle); _anchor = 0; }
                _portal.SetLandscape(_selectedMountain);
                _busy = false; _mode = Mode.Browse; _portal.calibrationHidden = false; _portal.showDoorLeaf = _previous.leaf;
                _portal.frameMode = _previous.frame; _portal.UpdatePortalState();
                _status = _persistent ? "saved" : "session"; _noticeUntil = 0; HideMarks();
                _portal.SaveCalibration(); PortalControllerInput.Pulse(true);
            }
        }
    }
    async Task Prepare()
    {
        try
        {
            if (Application.isEditor || Application.platform != RuntimePlatform.Android) return;
            PicoPassthroughSetup.RequestEnable();
            using (var timeout = CancellationTokenSource.CreateLinkedTokenSource(_lifetime.Token))
            {
                timeout.CancelAfter(10000);
                var startTask = PXR_MixedReality.StartSenseDataProvider(PxrSenseDataProviderType.SpatialAnchor, timeout.Token);
                if (await Task.WhenAny(startTask, Task.Delay(10500, _lifetime.Token)) != startTask) throw new TimeoutException("anchor provider startup");
                _providerReady = await startTask == PxrResult.SUCCESS;
                Debug.Log("[DoorCorner] anchor provider ready=" + _providerReady);
                if (!_providerReady || this == null) return;
                var json = PlayerPrefs.GetString(PlacementKey, "");
                if (string.IsNullOrEmpty(json)) return;
                var saved = JsonUtility.FromJson<SavedPlacement>(json);
                if (!Guid.TryParse(saved.uuid, out Guid uuid) || saved.width < .35f || saved.height < .5f) return;
                var query = await PXR_MixedReality.QuerySpatialAnchorAsync(new[] { uuid }, timeout.Token);
                if (query.result != PxrResult.SUCCESS || this == null) return;
                foreach (var h in query.anchorHandleList)
                {
                    if (PXR_MixedReality.GetAnchorUuid(h, out var id) == PxrResult.SUCCESS && id == uuid)
                    { _anchor = h; _saved = saved; _persistent = true; break; }
                    PXR_MixedReality.DestroyAnchor(h);
                }
            }
        }
        catch (Exception e) { Debug.LogWarning("[DoorCorner] startup: " + e.Message); }
    }
    void HideMarks() { foreach (var mark in _marks) mark.gameObject.SetActive(false); _outline.enabled = false; }
    Transform Sphere(string name, Color color, float diameter)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere); go.name = name;
        if (Application.isPlaying) Destroy(go.GetComponent<Collider>()); else DestroyImmediate(go.GetComponent<Collider>());
        go.transform.SetParent(transform,false); go.transform.localScale = Vector3.one * diameter;
        var material = new Material(_material); material.color = color; go.GetComponent<Renderer>().sharedMaterial = material;
        return go.transform;
    }
    void OnApplicationPause(bool paused)
    {
        _paused=paused; ResetInputEdges();
        Debug.Log($"[DoorCorner] pause={paused}; retained {ProgressSummary}");
    }
    void OnApplicationFocus(bool focused)
    {
        _focused=focused; ResetInputEdges();
        Debug.Log($"[DoorCorner] focus={focused}; retained {ProgressSummary}");
    }
    void ResetInputEdges()
    {
        // A trigger already held on return must be released before it can record again.
        _lastRight=default; _lastLeft=default; _rayFresh=false;
    }
    void OnDestroy()
    {
        _lifetime.Cancel();
        if (_guide != null) Destroy(_guide.gameObject);
        if (_anchor != 0) PXR_MixedReality.DestroyAnchor(_anchor);
        if (Instance == this) Instance = null;
    }
}
