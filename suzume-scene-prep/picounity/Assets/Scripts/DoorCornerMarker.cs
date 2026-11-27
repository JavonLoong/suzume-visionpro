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
    enum Mode { Ready, Guide, Collect, Preview, Browse, Tune }
    [Serializable] class SavedPlacement { public string uuid; public float width, height; public int version; public Vector3[] corners; }
    struct PreviousPlacement
    {
        public Vector3 position; public float yaw, width, height; public Quaternion rotation; public Vector3[] corners;
        public PortalConfig.FrameMode frame; public bool leaf, fullView;
    }
    public static DoorCornerMarker Instance { get; private set; }
    public bool IsEditing => _mode == Mode.Collect || _mode == Mode.Preview || _mode == Mode.Tune;
    public bool IsTuning => _mode == Mode.Tune;
    public int AdjustmentTarget => _tuneTarget;
    public bool IsBrowsing => _mode == Mode.Browse;
    public bool IsBusy => _busy;
    public bool AnchorProviderReady => _providerReady;
    public bool IsGuiding => _mode == Mode.Guide;
    public bool CanRunGuided => IsGuiding && !_busy && !_paused && _focused;
    public string ProgressSummary => $"mode={_mode} corners={_count} firstRay={_hasFirstRay}";
    bool _paused, _focused = true;
    public bool IsInitialized { get; private set; }
    public bool CanControlPhysicalDoor => IsInitialized && IsBrowsing && !_busy && !_paused && _focused;
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
    LineRenderer _imageCandidate;
    float _candidateUntil;
    Vector3[] _candidateCorners, _tuneBefore;
    Mode _tuneModeBefore;
    bool _tuneHiddenBefore;
    int _tuneTarget;
    bool _fine=true, _tuneTriggerReleased, _stickNeutral=true, _leftStickReady, _rightStickReady;
    float _repeatAt;
    Vector3 _adjustRight, _adjustForward;
    public bool HasImageCandidate => _imageCandidate != null && _imageCandidate.enabled;
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
    bool _previousWasBrowse, _selectedMountain, _automatic;
    bool _automaticPreviewReleased;
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
        if(_portal==null) { Debug.LogError("[DoorCorner] PortalManager missing; initialization stopped"); enabled=false; return; }
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
        _imageCandidate = new GameObject("DetectedDoorCandidate").AddComponent<LineRenderer>();
        _imageCandidate.transform.SetParent(transform,false);_imageCandidate.useWorldSpace=true;
        _imageCandidate.sharedMaterial=new Material(_material);_imageCandidate.sharedMaterial.color=new Color(1f,.65f,.12f);
        _imageCandidate.positionCount=5;_imageCandidate.enabled=false;
        _guide = new GameObject("PortalGuide").AddComponent<PortalGuideView>();
        if (Camera.main != null) _guide.Initialize(Camera.main);
        IsInitialized=true;
        Debug.Log("[DoorCorner] initialized Ready; left X enters manual placement");
        _prepareTask = Prepare();
    }
    void Update()
    {
        if (_imageCandidate != null && (!CanRunGuided || Time.unscaledTime > _candidateUntil)) _imageCandidate.enabled=false;
        if (_portal == null || !IsInitialized) return;
        ProcessInput(PortalControllerInput.Read(true),PortalControllerInput.Read(false));
    }
    void ProcessInput(PortalControllerInput.Hand right,PortalControllerInput.Hand left)
    {
        if(!IsInitialized)return;
        // Preserve the selected corners/ray across sleep or a system dialog.
        if (_paused || !_focused) { _rayFresh=false; return; }
        if (_mode == Mode.Preview && _automatic && right.tracked && !right.trigger) _automaticPreviewReleased = true;
        if (!_busy && Rise(right.stickClick,_lastRight.stickClick,right.tracked,_lastRight.tracked)
            && (_mode==Mode.Preview || IsBrowsing)) BeginAdjustment();
        if (IsTuning)
        {
            if(!_busy) ProcessAdjustment(right,left);
            _lastRight=right;_lastLeft=left;
            _guide?.Show(_busy?"busy":CurrentStatus(),true,_selectedMountain,PortalGuideView.Context.Placement);
            return;
        }
        UpdateRay(right);
        if (!_busy)
        {
            if (!(IsBrowsing && PicoDoorBleLink.Active) && Rise(right.primary, _lastRight.primary, right.tracked, _lastRight.tracked))
            {
                _selectedMountain=!_selectedMountain;
                // During placement, choose the next landscape without rebuilding geometry
                // or replacing the current step. It becomes visible only on confirmation.
                if(IsBrowsing) { _portal.SetLandscape(_selectedMountain);Notice(_selectedMountain ? "mountain" : "flat", 2f); }
                PortalControllerInput.Pulse(true);
            }
            if (Rise(left.primary, _lastLeft.primary, left.tracked, _lastLeft.tracked)) Begin();
            if (!(IsBrowsing && PicoDoorBleLink.Active) && Rise(right.secondary, _lastRight.secondary, right.tracked, _lastRight.tracked))
            {
                if (IsEditing || IsGuiding) Cancel(); else _help = !_help;
            }
            if (Rise(left.secondary, _lastLeft.secondary, left.tracked, _lastLeft.tracked) && !IsEditing && !IsGuiding)
            {
                if(_mode==Mode.Ready) RestoreSaved();
                else if(_portal.physicalOpeningOnly) { _help=!_help; }
                else
                {
                    _portal.frameMode = _portal.frameMode == PortalConfig.FrameMode.Reference ? PortalConfig.FrameMode.Occlusion : PortalConfig.FrameMode.Reference;
                    _portal.UpdatePortalState();
                    Notice(_portal.frameMode == PortalConfig.FrameMode.Reference ? "frame_on" : "frame_off", 2f);
                }
            }
            if (IsEditing && Rise(left.trigger, _lastLeft.trigger, left.tracked, _lastLeft.tracked)) Undo();
            else if ((!IsBrowsing || DoorAutoLocator.Instance != null) && PicoPassthroughSetup.IsReady && Rise(right.trigger, _lastRight.trigger, right.tracked, _lastRight.tracked))
            {
                bool froze=IsGuiding && HasImageCandidate && FreezeCandidate();
                bool guided = froze || ((_mode == Mode.Ready || IsGuiding || IsBrowsing) && BeginGuided(right));
                if (!guided && _mode==Mode.Ready) Begin();
                if (!guided && _mode == Mode.Preview && (!_automatic || _automaticPreviewReleased)) _ = Confirm();
                else if (!guided && _mode == Mode.Collect && _count < 4)
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
                ApplySaved(PortalControllerInput.ToWorld(pos), PortalControllerInput.ToWorld(rot));
                _status = "saved";
            }
            else _status = "locating";
        }
        string status = !IsBrowsing && !PicoPassthroughSetup.IsReady ? "passthrough_wait" : (_busy ? "busy" : (!IsBrowsing && !right.tracked ? "wait" : CurrentStatus()));
        _guide?.Show(status, _help || !IsBrowsing || _busy || (_noticeUntil > Time.unscaledTime), _selectedMountain,
            _mode==Mode.Ready ? PortalGuideView.Context.Ready : (IsBrowsing ? PortalGuideView.Context.Browse :
                (IsGuiding || (_mode == Mode.Preview && _automatic) ? PortalGuideView.Context.Guided : PortalGuideView.Context.Placement)));
        _guide?.ShowRayGap(_solution.gap,_mode==Mode.Collect && _hasFirstRay && _rayHit);
    }
    void UpdateRay(PortalControllerInput.Hand hand)
    {
        if(_firstLine==null||_laser==null||_tip==null||_firstNearest==null||_secondNearest==null||_nearestBridge==null)return;
        bool active=(_mode==Mode.Ready || IsGuiding || _mode==Mode.Collect) && _count<4 && !_busy;
        _rayFresh=false;
        if(!_hasFirstRay) _rayHit=false;
        _firstLine.enabled=(_mode==Mode.Collect && _count<4 && _hasFirstRay);
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
        _laser.enabled=active&&_hasDisplayRay&&(!IsGuiding || !HasImageCandidate);
        if(_laser.enabled)
        {
            _laser.SetPosition(0,_displayRay.origin);
            _laser.SetPosition(1,_displayRay.GetPoint(_rayHit ? Mathf.Max(.3f,_solution.secondDistance) : (_mode==Mode.Collect ? DoorRayIntersection.MaximumDistance : 1.5f)));
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
            _firstLine.SetPosition(1,_firstRay.GetPoint(_rayHit ? Mathf.Max(.3f,_solution.firstDistance) : (_mode==Mode.Collect ? DoorRayIntersection.MaximumDistance : 1.5f)));
        }
        _tip.gameObject.SetActive(active&&_rayHit);
        _firstNearest.gameObject.SetActive(active&&_rayHit);_secondNearest.gameObject.SetActive(active&&_rayHit);
        _nearestBridge.enabled=active&&_rayHit;
    }
    static bool Rise(bool now, bool was, bool tracked, bool wasTracked) => tracked && wasTracked && now && !was;
    string CurrentStatus()
    {
        if (_noticeUntil > Time.unscaledTime) return _notice;
        if(IsTuning)return "tune_"+_tuneTarget+(_fine?"_fine":"_coarse");
        if(IsGuiding&&HasImageCandidate)return "guided_candidate";
        if (_mode == Mode.Ready) return "ready";
        if (IsGuiding) return DoorAutoLocator.Instance != null ? DoorAutoLocator.Instance.GuideStatus : "guided_camera";
        if (_mode == Mode.Preview && _automatic) return "guided_preview";
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
    bool BeginGuided(PortalControllerInput.Hand hand)
    {
        var locator = DoorAutoLocator.Instance;
        Ray ray = PortalControllerInput.AimRay(hand);
        if (locator == null || !locator.BeginGuided(ray)) return false;
        if (!IsEditing && !IsGuiding)
        {
            _previousWasBrowse = IsBrowsing;
            _previous = new PreviousPlacement { position = _portal.portalPosition, yaw = _portal.portalYaw, rotation=_portal.transform.rotation, corners=_portal.GetWorldCorners(), width = _portal.portalWidth,
                height = _portal.portalHeight, frame = _portal.frameMode, leaf = _portal.showDoorLeaf, fullView = _portal.fullMeadowView };
        }
        _mode = Mode.Guide; _count = 0; _automatic = false; _help = true; _noticeUntil = 0;
        _firstRay = ray; _hasFirstRay = false; _rayHit = false; _hasDisplayRay = false;
        _portal.calibrationHidden = true; _portal.fullMeadowView = false; _portal.UpdatePortalState();
        HideMarks(); PicoPassthroughSetup.RequestEnable(); PortalControllerInput.Pulse(true);
        Debug.Log("[DoorCorner] controller-guided camera search started");
        return true;
    }
    void Begin()
    {
        if (_imageCandidate != null) _imageCandidate.enabled=false;
        if (!IsEditing && !IsGuiding)
        {
            _previousWasBrowse=IsBrowsing;
            _previous = new PreviousPlacement { position = _portal.portalPosition, yaw = _portal.portalYaw, rotation=_portal.transform.rotation, corners=_portal.GetWorldCorners(), width = _portal.portalWidth, height = _portal.portalHeight, frame = _portal.frameMode, leaf = _portal.showDoorLeaf, fullView = _portal.fullMeadowView };
        }
        DoorAutoLocator.Instance?.CancelGuided();
        _mode = Mode.Collect; _count = 0; _help = true; _noticeUntil = 0;_hasFirstRay=false;_rayHit=false;_hasDisplayRay=false;
        _automatic = false; _outline.startWidth = _outline.endWidth = .006f;
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
            if (Vector3.Distance(point, _corners[i]) < .008f) { Notice("error_duplicate"); return; }
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
        _portal.SetWorldCorners(_corners);
        _outline.SetPositions(new[] { _corners[0], _corners[1], _corners[3], _corners[2], _corners[0] });
        _outline.enabled = true;
        Debug.Log($"[DoorCorner] preview width={_fit.width:F3} height={_fit.height:F3}");
    }
    // Shows a pose found without the controller as the usual preview outline; the trigger then
    // confirms it and stores the anchor, the secondary button or the left trigger rejects it.
    // Amber is a camera candidate. The first trigger freezes it; a separate trigger confirms display.
    public bool ShowDetectedDoor(DoorPoseSolver.Solution pose, float width, float height)
    {
        if (!CanRunGuided || _imageCandidate == null || width<=0 || height<=0) return false;
        Vector3 side=pose.rotation*Vector3.right*(width*.5f), rise=pose.rotation*Vector3.up*height;
        Vector3 bl=pose.position+side,br=pose.position-side;
        _candidateCorners=DoorQuadPlacement.Rectangle(pose.position,pose.rotation,width,height);
        _imageCandidate.SetPositions(new[]{bl,br,br+rise,bl+rise,bl});
        _imageCandidate.startWidth=_imageCandidate.endWidth=Mathf.Min(.002f,width*.035f);
        _candidateUntil=Time.unscaledTime+.6f;_imageCandidate.enabled=true;
        return true;
    }
    public bool PreviewAutomaticPlacement(Vector3 center, Quaternion rotation, float width, float height)
    {
        if (_portal == null || _busy || _paused || !_focused || IsEditing || width <= 0 || height <= 0) return false;
        if (_imageCandidate != null) _imageCandidate.enabled=false;
        if (!IsGuiding)
        {
            _previousWasBrowse = IsBrowsing;
            _previous = new PreviousPlacement { position = _portal.portalPosition, yaw = _portal.portalYaw, rotation=_portal.transform.rotation, corners=_portal.GetWorldCorners(), width = _portal.portalWidth, height = _portal.portalHeight, frame = _portal.frameMode, leaf = _portal.showDoorLeaf, fullView = _portal.fullMeadowView };
        }
        _automaticPreviewReleased = false;
        _automatic = true; _hasFirstRay = false; _rayHit = false; _hasDisplayRay = false;
        _fit = new DoorCalibrationMath.Placement { center = center, rotation = rotation, width = width, height = height };
        Vector3 side = rotation * Vector3.right * (width * .5f), rise = rotation * Vector3.up * height;
        _corners[0] = center + side; _corners[1] = center - side; _corners[2] = center + side + rise; _corners[3] = center - side + rise;
        _count = 4; _mode = Mode.Preview; _status = "preview"; _noticeUntil = 0; _help = true;
        _portal.calibrationHidden = true; _portal.fullMeadowView = false;
        Apply(center, rotation, width, height);
        _portal.SetWorldCorners(_corners);
        PicoPassthroughSetup.RequestEnable();
        foreach (var mark in _marks) mark.gameObject.SetActive(false);
        _outline.startWidth = _outline.endWidth = Mathf.Min(.006f, width * .05f);
        _outline.SetPositions(new[] { _corners[0], _corners[1], _corners[3], _corners[2], _corners[0] });
        _outline.enabled = true;
        PortalControllerInput.Pulse(true);
        Debug.Log($"[DoorCorner] automatic preview width={width:F4} height={height:F4} at {center:F4}");
        return true;
    }
    bool FreezeCandidate()
    {
        if(_candidateCorners==null||Time.unscaledTime>_candidateUntil)return false;
        var points=(Vector3[])_candidateCorners.Clone();
        if(!DoorQuadPlacement.TryFit(points,out var fit))return false;
        if(!PreviewAutomaticPlacement(fit.center,fit.rotation,fit.width,fit.height))return false;
        Array.Copy(points,_corners,4);_fit=fit;
        _portal.SetWorldCorners(_corners);UpdateAdjustmentOutline(false);
        DoorAutoLocator.Instance?.CancelGuided();
        _status="frozen_preview";Notice("frozen_preview",3f);
        Debug.Log("[DoorCorner] user froze recognized candidate; waiting for explicit display confirmation");
        return true;
    }
    void ApplySaved(Vector3 position,Quaternion rotation)
    {
        Apply(position,rotation,_saved.width,_saved.height);
        var points=_saved.corners!=null&&_saved.corners.Length==4
            ?DoorQuadPlacement.ToWorld(_saved.corners,position,rotation)
            :DoorQuadPlacement.Rectangle(position,rotation,_saved.width,_saved.height);
        Array.Copy(points,_corners,4);_count=4;
        _fit=new DoorCalibrationMath.Placement{center=position,rotation=rotation,width=_saved.width,height=_saved.height};
        _portal.SetWorldCorners(points);
    }
    void BeginAdjustment()
    {
        if(_busy||(_mode!=Mode.Preview&&!IsBrowsing))return;
        _tuneModeBefore=_mode;
        if(IsBrowsing)
        {
            _previousWasBrowse=true;
            _previous=new PreviousPlacement{position=_portal.portalPosition,yaw=_portal.portalYaw,rotation=_portal.transform.rotation,
                width=_portal.portalWidth,height=_portal.portalHeight,corners=_portal.GetWorldCorners(),
                frame=_portal.frameMode,leaf=_portal.showDoorLeaf,fullView=_portal.fullMeadowView};
            Array.Copy(_portal.GetWorldCorners(),_corners,4);
        }
        if(!DoorQuadPlacement.TryFit(_corners,out _fit))return;
        _tuneHiddenBefore=_portal.calibrationHidden;
        _portal.calibrationHidden=false;
        _portal.UpdatePortalState();
        _tuneBefore=(Vector3[])_corners.Clone();_tuneTarget=0;_fine=true;_count=4;
        _tuneTriggerReleased=false;_stickNeutral=false;_leftStickReady=false;_rightStickReady=false;_repeatAt=0;_noticeUntil=0;
        _adjustForward=Camera.main!=null?Vector3.ProjectOnPlane(Camera.main.transform.forward,Vector3.up).normalized:Vector3.forward;
        if(_adjustForward.sqrMagnitude<.5f)_adjustForward=Vector3.forward;
        _adjustRight=Vector3.Cross(Vector3.up,_adjustForward).normalized;
        _mode=Mode.Tune;DoorAutoLocator.Instance?.CancelGuided();
        _laser.enabled=false;_firstLine.enabled=false;_imageCandidate.enabled=false;
        UpdateAdjustmentOutline(true);PortalControllerInput.Pulse(true);
    }
    void ProcessAdjustment(PortalControllerInput.Hand right,PortalControllerInput.Hand left)
    {
        if(right.tracked&&!right.trigger)_tuneTriggerReleased=true;
        if(Rise(right.secondary,_lastRight.secondary,right.tracked,_lastRight.tracked))
        {
            Array.Copy(_tuneBefore,_corners,4);DoorQuadPlacement.TryFit(_corners,out _fit);
            Apply(_fit.center,_fit.rotation,_fit.width,_fit.height);_portal.SetWorldCorners(_corners);
            _mode=_tuneModeBefore;_noticeUntil=0;
            _portal.calibrationHidden=_tuneHiddenBefore;_portal.UpdatePortalState();
            if(IsBrowsing)HideMarks();else UpdateAdjustmentOutline(false);
            return;
        }
        if(Rise(right.primary,_lastRight.primary,right.tracked,_lastRight.tracked))_tuneTarget=(_tuneTarget+1)%5;
        if(Rise(left.primary,_lastLeft.primary,left.tracked,_lastLeft.tracked))_tuneTarget=(_tuneTarget+4)%5;
        if(Rise(left.secondary,_lastLeft.secondary,left.tracked,_lastLeft.tracked))_fine=!_fine;
        if(_tuneTriggerReleased&&Rise(right.trigger,_lastRight.trigger,right.tracked,_lastRight.tracked)) { _=Confirm();return; }
        float Axis(float v)=>Mathf.Abs(v)>.65f?Mathf.Sign(v):0;
        if(!left.tracked)_leftStickReady=false;else if(left.stick.sqrMagnitude<.1f)_leftStickReady=true;
        if(!right.tracked)_rightStickReady=false;else if(right.stick.sqrMagnitude<.1f)_rightStickReady=true;
        Vector3 axis=(left.tracked&&_leftStickReady?_adjustRight*Axis(left.stick.x)+_adjustForward*Axis(left.stick.y):Vector3.zero)
            +(right.tracked&&_rightStickReady?Vector3.up*Axis(right.stick.y):Vector3.zero);
        if(axis==Vector3.zero){_stickNeutral=true;_repeatAt=0;}
        else if(_stickNeutral||(_repeatAt>0&&Time.unscaledTime>=_repeatAt))
        {
            Vector3 delta=axis*(_fine?.0001f:.0005f);
            TryAdjust(_tuneTarget,delta);
            _repeatAt=Time.unscaledTime+(_stickNeutral?.35f:.09f);_stickNeutral=false;
        }
        UpdateAdjustmentOutline(true);
    }
    public bool TryAdjust(int target,Vector3 delta)
    {
        if(!IsTuning||_busy||_paused||!_focused||target<0||target>4||delta.magnitude>.05f)return false;
        var next=(Vector3[])_corners.Clone();
        for(int i=0;i<4;i++)if(target==0||target==i+1)next[i]+=delta;
        if(!DoorQuadPlacement.TryFit(next,out var fit)){Notice("tune_invalid",1f);return false;}
        Array.Copy(next,_corners,4);_fit=fit;_noticeUntil=0;
        Apply(fit.center,fit.rotation,fit.width,fit.height);_portal.SetWorldCorners(_corners);
        return true;
    }
    void UpdateAdjustmentOutline(bool marks)
    {
        _outline.SetPositions(new[]{_corners[0],_corners[1],_corners[3],_corners[2],_corners[0]});
        _outline.startWidth=_outline.endWidth=Mathf.Clamp(_fit.width*.003f,.00008f,.0003f);_outline.enabled=true;
        for(int i=0;i<4;i++)
        {
            _marks[i].position=_corners[i];_marks[i].localScale=Vector3.one*Mathf.Clamp(_fit.width*.02f,.0005f,.003f);
            _marks[i].GetComponent<Renderer>().sharedMaterial.color=(_tuneTarget==0||_tuneTarget==i+1)?new Color(1f,.7f,.15f):new Color(.55f,.65f,.7f);
            _marks[i].gameObject.SetActive(marks);
        }
    }
    void Undo()
    {
        if (_automatic) { Cancel(); return; }
        if(_hasFirstRay) { _hasFirstRay=false;_rayHit=false;_noticeUntil=0;PortalControllerInput.Pulse(false);return; }
        if (_count == 0) return;
        _count--; _marks[_count].gameObject.SetActive(false); _mode = Mode.Collect; _noticeUntil = 0;
        _firstRay=_firstRays[_count];_hasFirstRay=true;_rayHit=false;
        _portal.calibrationHidden = true; _outline.enabled = false; PortalControllerInput.Pulse(false);
        _portal.UpdatePortalState();
    }
    void Cancel()
    {
        DoorAutoLocator.Instance?.CancelGuided();
        _mode = _previousWasBrowse ? Mode.Browse : Mode.Ready; _automatic = false;
        _portal.calibrationHidden = !IsBrowsing;_hasFirstRay=false;_rayHit=false;_hasDisplayRay=false;_count=0;
        if(IsBrowsing) _selectedMountain=_portal.mountainLandscape;
        _portal.frameMode = _previous.frame; _portal.showDoorLeaf = _previous.leaf; _portal.fullMeadowView = _previous.fullView;
        Apply(_previous.position, _previous.rotation, _previous.width, _previous.height);
        _portal.SetWorldCorners(_previous.corners);
        HideMarks(); _status = _persistent ? "saved" : "intro"; Notice(IsBrowsing ? "cancelled" : "ready");
    }
    void RestoreSaved()
    {
        if(_anchor==0 || _saved==null) { Notice("no_saved");return; }
        if(PXR_MixedReality.LocateAnchor(_anchor,out var position,out var rotation)!=PxrResult.SUCCESS) { Notice("locating");return; }
        _portal.SetLandscape(_selectedMountain);
        _portal.fullMeadowView=false;_portal.calibrationHidden=false;_mode=Mode.Browse;
        ApplySaved(PortalControllerInput.ToWorld(position),PortalControllerInput.ToWorld(rotation));
        _status="saved";_noticeUntil=0;
        Debug.Log("[DoorCorner] explicitly restored saved placement");
    }
    void Apply(Vector3 center, Quaternion rotation, float width, float height)
    {
        _portal.portalPosition = center; _portal.portalYaw = rotation.eulerAngles.y;
        _portal.useFullRotation=true; _portal.portalRotation=rotation;
        _portal.portalWidth = width; _portal.portalHeight = height; _portal.UpdatePortalState();
    }
    async Task Confirm()
    {
        DoorAutoLocator.Instance?.CancelGuided();
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
                _saved = new SavedPlacement { uuid = create.uuid.ToString(), width = _fit.width, height = _fit.height, version=4,
                    corners=DoorQuadPlacement.ToLocal(_corners,_fit.center,_fit.rotation) };
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
                Apply(_fit.center,_fit.rotation,_fit.width,_fit.height);_portal.SetWorldCorners(_corners);
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
                if (saved==null||!Guid.TryParse(saved.uuid, out Guid uuid)||!(saved.width>=.008f&&saved.width<=3f&&saved.height>=.015f&&saved.height<=3.5f)) return;
                if(saved.corners!=null&&!DoorQuadPlacement.TryFit(saved.corners,out _))return;
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
    void HideMarks() { foreach (var mark in _marks) mark.gameObject.SetActive(false); _outline.enabled = false; if (_imageCandidate != null) _imageCandidate.enabled=false; }
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
        _paused=paused; ResetInputEdges();if(paused){_stickNeutral=false;_repeatAt=0;_tuneTriggerReleased=false;_leftStickReady=false;_rightStickReady=false;}
        if (paused && _imageCandidate != null) _imageCandidate.enabled=false;
        Debug.Log($"[DoorCorner] pause={paused}; retained {ProgressSummary}");
    }
    void OnApplicationFocus(bool focused)
    {
        _focused=focused; ResetInputEdges();if(!focused){_stickNeutral=false;_repeatAt=0;_tuneTriggerReleased=false;_leftStickReady=false;_rightStickReady=false;}
        if (!focused && _imageCandidate != null) _imageCandidate.enabled=false;
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
