using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 铃芽之旅 · 梦幻门场景组装与运行时校准管理器（Unity / PICO 4 Ultra 版）。
///
/// 核心机制（对齐 Apple Vision Pro 版与 v32/v37/v56 节点旋转体系）：
/// 1. 门洞遮罩（PortalMask.shader，Queue=Geometry-50）：在 0.879×2.10m 门洞开口写入 Stencil=1，不输出颜色与深度。
/// 2. 实体门框遮挡（DoorOcclusion.shader，Queue=Geometry-40）：当处于「门框仅作遮挡」模式时，将门框区域 Stencil 重置为 0 并写入深度。
/// 3. 三层刚性门轴与双空间同步门扇（对齐 v32 integrate_door_v32.py & browser-door.js）：
///    - 顶层：RigidHingeCompensation（抵消父级非均匀 X 缩放，保证门扇在 0°~120° 任意角度下宽度与厚度绝对刚性不拉伸）；
///    - 庭院侧铰链：AnimatedDoorLeafAndHinges（位于右侧门柱合页轴心 X=-0.43728m, Z=+0.03397m，裁剪保留门外 Z>=0 半空间，Queue=Geometry-30）；
///    - 异世界同步铰链：SynchronizedNightDoorLeaf（与庭院铰链实时同步同角度旋转，裁剪保留门内 Z<=0 半空间且仅在 Stencil==1 门洞内渲染，Queue=Geometry+15）；
///    - 门把手追踪锚点：DoorKnobTarget（位于门扇局部 X=+0.4125m, Y=0.955m, Z=+0.1334m，随门扇旋转划出真实圆弧）。
/// 4. 铃芽 20 骨骼绑定与右手推门二连杆 IK（SuzumeRigController.cs）：
///    - 自动绑定 Character.fbx 内的 SuzumeHunyuanRig 20 根骨骼节点（SkinnedMeshRenderer）；
///    - 支持「门后 2.7m 花海远眺」与「门槛右手推门联动（余弦定理二连杆解析 IK 实时追踪 DoorKnobTarget）」两种姿态模式。
/// </summary>
[ExecuteAlways]
public class PortalManager : MonoBehaviour
{
    [Header("门户核心材质")]
    public Material portalMaskMaterial;
    public Material portalTargetMaterial;

    [Header("真实资产（VisionPro 同源 FBX 资产）")]
    [Tooltip("门框模型（Assets/Models/DoorFrame.fbx）")]
    public GameObject doorPrefab;
    [Tooltip("独立可开合门扇模型（Assets/Models/DoorLeaf.fbx）")]
    public GameObject doorLeafPrefab;
    [Tooltip("门后梦幻花海世界模型（Assets/Models/DreamWorld.fbx）")]
    public GameObject dreamWorldPrefab;
    [Tooltip("20 骨骼绑定铃芽角色模型（Assets/Models/Character.fbx）")]
    public GameObject characterPrefab;

    [Header("实机对齐与体验参数")]
    [Tooltip("门洞净高（米），默认 2.10m；变化时净宽与花海世界按 v56 原比例同步缩放")]
    [Range(0.5f, 3.5f)]
    public float portalHeight = PortalConfig.BaseDoorHeight;
    [Tooltip("四点定位测得的门洞净宽；0 表示沿用模型比例")]
    public float portalWidth;
    public bool mountainLandscape;
    [System.NonSerialized] public bool calibrationHidden;

    [Tooltip("门槛地面中心位置（米）")]
    public Vector3 portalPosition = PortalConfig.PortalPosition;

    [Tooltip("门朝向旋转角（度）")]
    [Range(-180f, 180f)]
    public float portalYaw = PortalConfig.PortalRotationY;

    [Tooltip("门后花海与角色曝光亮度倍率")]
    [Range(0.2f, 3.0f)]
    public float lightMultiplier = PortalConfig.LightMultiplier;

    [Tooltip("常世星河、晚霞与发光花海奇观氛围强度")]
    [Range(0.2f, 2.5f)]
    public float atmosphereIntensity = PortalConfig.AtmosphereIntensity;

    [Tooltip("花海与草叶微风摆动强度")]
    [Range(0f, 2.5f)]
    public float windStrength = PortalConfig.WindStrength;

    [Tooltip("虚拟门框显示模式：Reference=显示对齐门框，Occlusion=门框仅作遮挡（MR真机用），Hidden=隐藏")]
    public PortalConfig.FrameMode frameMode = PortalConfig.FrameMode.Reference;

    [Header("双空间刚性门轴旋转控制（v32 / v56）")]
    [Tooltip("是否显示双空间可活动虚拟门扇")]
    public bool showDoorLeaf = PortalConfig.DefaultShowDoorLeaf;

    [Tooltip("门扇当前开启角度（度，0°=完全关闭，88.8°=v32/v56 电影开门角度 1.55 rad）")]
    [Range(0f, 120f)]
    public float doorOpenAngle = PortalConfig.DoorOpenAngle;

    [Tooltip("目标开关门状态（点击开门/关门按钮时按 1-exp(-dt*5) 阻尼平滑过渡）")]
    public bool targetDoorOpen = true;
    public bool animateDoorSmoothly = false;

    [Header("铃芽 20 骨骼与姿态控制（v16 / v32）")]
    [Tooltip("是否显示铃芽角色")]
    public bool showCharacter = PortalConfig.UseCharacter;

    [Tooltip("铃芽姿态模式：MeadowLookout=门后2.7m花海远眺，MovieDoorOpening=门槛右手推门IK联动")]
    public SuzumeRigController.PoseMode characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;

    [Range(-45f, 45f)]
    public float characterHeadYaw = 0f;
    [Range(-30f, 30f)]
    public float characterHeadPitch = 0f;
    [Range(-30f, 90f)]
    public float characterRightArmLift = 0f;

    [Tooltip("完整花海检查模式（关闭门洞裁剪，360° 查看门后世界）")]
    public bool fullMeadowView = false;

    [Header("辅助选项")]
    public bool buildVirtualDoor = false;
    public bool buildPreviewWall = false;
    public bool showOutsideReferenceFloor = true;
    public Vector3 dreamWorldOffset = Vector3.zero;
    public float dreamWorldScale = 0f;

    const string MaskName = "PortalMask";
    const string DreamName = "DreamWorld";
    const string CharacterName = "SuzumeCharacter";
    const string DoorName = "DoorAssembly";
    const string RigidHingeCompName = "RigidHingeCompensation_v32";
    const string DayDoorHingeName = "AnimatedDoorLeafAndHinges";
    const string NightDoorHingeName = "SynchronizedNightDoorLeaf";
    const string DoorKnobName = "DoorKnobTarget";
    const string OutsideFloorName = "OutsideReferenceFloor";
    const string CalibPrefKey = "SuzumePortal.Calibration.V2";

    GameObject _maskGo;
    GameObject _dreamGo;
    GameObject _characterGo;
    SuzumeRigController _rigController;
    GameObject _doorGo;
    GameObject _rigidHingeCompGo;
    GameObject _dayDoorHingeGo;
    GameObject _nightDoorHingeGo;
    Transform _doorKnobTarget;
    GameObject _outsideFloorGo;

    public SuzumeRigController RigController => _rigController;
    public Transform DoorKnobTarget => _doorKnobTarget;
    public Transform DayDoorHinge => _dayDoorHingeGo != null ? _dayDoorHingeGo.transform : null;
    public Transform NightDoorHinge => _nightDoorHingeGo != null ? _nightDoorHingeGo.transform : null;

    void OnEnable()
    {
        if (!Application.isPlaying && !PortalConfig.BuildInEditMode) return;
        EnsureBuilt();
        UpdatePortalState();
    }

    void Start()
    {
        if(!Application.isEditor && Application.platform==RuntimePlatform.Android) calibrationHidden=true;
        if (Application.isPlaying) mountainLandscape = PlayerPrefs.GetInt("SuzumePortal.Landscape", 0) == 1;
        QualitySettings.globalTextureMipmapLimit = 0;
        QualitySettings.anisotropicFiltering = AnisotropicFiltering.ForceEnable;
        if (QualitySettings.antiAliasing < 4) QualitySettings.antiAliasing = 8;

        if (Application.isPlaying)
        {
            BuildPortal();
        }
        else
        {
            EnsureBuilt();
        }
        UpdatePortalState();
    }

    void Update()
    {
        EnsureBuilt();
        if (animateDoorSmoothly)
        {
            float desired = targetDoorOpen ? PortalConfig.MovieDoorOpenAngle : 0f;
            float dt = Application.isPlaying ? Mathf.Min(Time.deltaTime, 0.05f) : 0.02f;
            float factor = 1f - Mathf.Exp(-dt * 5f);
            doorOpenAngle = doorOpenAngle + (desired - doorOpenAngle) * factor;
            if (Mathf.Abs(doorOpenAngle - desired) < 0.05f)
            {
                doorOpenAngle = desired;
                animateDoorSmoothly = false;
            }
        }
        UpdatePortalState();
    }

    /// <summary>
    /// 触发 v56 同款指数阻尼平滑开门 / 关门（0° <-> 88.8° / 1.55 rad）。
    /// </summary>
    public void ToggleDoorOpen(bool open)
    {
        showDoorLeaf = true;
        targetDoorOpen = open;
        animateDoorSmoothly = true;
    }

    public void EnsureBuilt()
    {
        var existingMask = transform.Find(MaskName);
        var existingDream = transform.Find(DreamName);
        var existingFloor = transform.Find(OutsideFloorName);
        bool floorNeedsUpgrade = existingFloor == null
            || existingFloor.Find("OutsideGridLines") != null
            || existingFloor.Find("CourtyardLushGrassBlades") == null;
        bool dreamNeedsUpgrade = existingDream == null
            || existingDream.Find(DreamWorldAtmosphere.RootName + "/" + DreamWorldAtmosphere.GrassName) == null;

        if (existingMask == null || dreamNeedsUpgrade || floorNeedsUpgrade)
        {
            BuildPortal();
        }
        else
        {
            _maskGo = existingMask.gameObject;
            _dreamGo = existingDream.gameObject;
            var ch = transform.Find(CharacterName);
            if (ch != null)
            {
                _characterGo = ch.gameObject;
                _rigController = _characterGo.GetComponent<SuzumeRigController>();
            }
            var dr = transform.Find(DoorName);
            if (dr != null) _doorGo = dr.gameObject;
            var comp = transform.Find(RigidHingeCompName);
            if (comp != null)
            {
                _rigidHingeCompGo = comp.gameObject;
                var d1 = comp.Find(DayDoorHingeName);
                if (d1 != null)
                {
                    _dayDoorHingeGo = d1.gameObject;
                    var knob = d1.Find("DoorLeafMesh/" + DoorKnobName);
                    if (knob != null) _doorKnobTarget = knob;
                }
                var d2 = comp.Find(NightDoorHingeName);
                if (d2 != null) _nightDoorHingeGo = d2.gameObject;
            }
            if (existingFloor != null) _outsideFloorGo = existingFloor.gameObject;
        }
    }

    public void BuildPortal()
    {
        Clear();

        // 1) 门洞遮罩（基准尺寸：0.878918m × 2.10m，底部在门槛 y=0，中心在 y=1.05m）
        _maskGo = BuildMask();
        MarkDontSave(_maskGo);

        // 2) 门框（DoorFrame.fbx 或回退程序化门框）
        if (doorPrefab != null)
        {
            _doorGo = Instantiate(doorPrefab);
            _doorGo.name = DoorName;
            _doorGo.transform.SetParent(transform, false);
            _doorGo.transform.localPosition = Vector3.zero;
            _doorGo.transform.localRotation = Quaternion.identity;
            _doorGo.transform.localScale = Vector3.one;
            OpenUpDoorway(_doorGo);
            MaterialMapper.ApplyDoorMaterials(_doorGo, frameMode);
            MarkDontSave(_doorGo);
        }
        else if (buildVirtualDoor)
        {
            _doorGo = DoorOcclusion.Build(transform);
            if (_doorGo != null) MarkDontSave(_doorGo);
        }

        // 3) v32/v56 三层刚性门扇铰链体系：
        //    RigidHingeCompensation_v32 -> [AnimatedDoorLeafAndHinges (庭院侧 Z>=0), SynchronizedNightDoorLeaf (异世界侧 Z<=0)]
        if (doorLeafPrefab != null)
        {
            _rigidHingeCompGo = new GameObject(RigidHingeCompName);
            _rigidHingeCompGo.transform.SetParent(transform, false);
            _rigidHingeCompGo.transform.localPosition = Vector3.zero;
            _rigidHingeCompGo.transform.localRotation = Quaternion.identity;
            _rigidHingeCompGo.transform.localScale = Vector3.one;

            Vector3 hingePos = new Vector3(PortalConfig.DoorHingeX, 0f, PortalConfig.DoorHingeZ);
            Vector3 meshOffset = -hingePos;

            // 3a) 庭院侧门扇铰链（Animated door leaf and hinges）
            _dayDoorHingeGo = new GameObject(DayDoorHingeName);
            _dayDoorHingeGo.transform.SetParent(_rigidHingeCompGo.transform, false);
            _dayDoorHingeGo.transform.localPosition = hingePos;
            _dayDoorHingeGo.transform.localRotation = Quaternion.Euler(0f, doorOpenAngle, 0f);

            var dayLeaf = Instantiate(doorLeafPrefab);
            dayLeaf.name = "DoorLeafMesh";
            dayLeaf.transform.SetParent(_dayDoorHingeGo.transform, false);
            dayLeaf.transform.localPosition = meshOffset;
            dayLeaf.transform.localRotation = Quaternion.identity;
            dayLeaf.transform.localScale = Vector3.one;

            // 在门扇上挂载真实门把手三维锚点（供铃芽右手二连杆 IK 实时追踪）
            var knobGo = new GameObject(DoorKnobName);
            knobGo.transform.SetParent(dayLeaf.transform, false);
            knobGo.transform.localPosition = PortalConfig.DoorKnobLocalPos;
            _doorKnobTarget = knobGo.transform;

            // 3b) 异世界侧同步门扇铰链（Synchronized night door leaf）
            _nightDoorHingeGo = new GameObject(NightDoorHingeName);
            _nightDoorHingeGo.transform.SetParent(_rigidHingeCompGo.transform, false);
            _nightDoorHingeGo.transform.localPosition = hingePos;
            _nightDoorHingeGo.transform.localRotation = Quaternion.Euler(0f, doorOpenAngle, 0f);

            var nightLeaf = Instantiate(doorLeafPrefab);
            nightLeaf.name = "DoorLeafNightMesh";
            nightLeaf.transform.SetParent(_nightDoorHingeGo.transform, false);
            nightLeaf.transform.localPosition = meshOffset;
            nightLeaf.transform.localRotation = Quaternion.identity;
            nightLeaf.transform.localScale = Vector3.one;

            MarkDontSave(_rigidHingeCompGo);
        }

        // 4) 门后梦幻花海世界（DreamWorld.fbx + 常世奇观氛围增强层 DreamWorldAtmosphere）
        BuildDreamWorld();

        // 5) 20 骨骼绑定铃芽角色（Character.fbx，身高 1.62m，挂载 SuzumeRigController）
        if (characterPrefab != null)
        {
            _characterGo = Instantiate(characterPrefab);
            _characterGo.name = CharacterName;
            _characterGo.transform.SetParent(transform, false);
            _characterGo.transform.localPosition = PortalConfig.CharacterOffset;
            _characterGo.transform.localRotation = Quaternion.Euler(0f, PortalConfig.CharacterYaw, 0f);
            _characterGo.transform.localScale = Vector3.one;

            _rigController = _characterGo.GetComponent<SuzumeRigController>();
            if (_rigController == null)
            {
                _rigController = _characterGo.AddComponent<SuzumeRigController>();
            }
            _rigController.EnsureBound();
            MarkDontSave(_characterGo);
        }

        // 6) 门外庭院真实感草坪与三维草丛（替代原本简陋的方格网地面，且严格限制在门外 Z>=0 庭院侧）
        _outsideFloorGo = BuildOutsideReferenceFloor();
        MarkDontSave(_outsideFloorGo);

        // 7) 应用门后世界与角色的 Stencil + 门洞裁剪平面 + 烘焙贴图与奇观氛围材质
        Vector4 clipPlane = ComputeWorldClipPlane();
        bool useStencil = !fullMeadowView && (Application.isPlaying || !PortalConfig.DisableStencilInEditMode);
        bool useClip = !fullMeadowView;

        MaterialMapper.ApplyPortalTarget(_dreamGo, portalTargetMaterial, useStencil, clipPlane, useClip, lightMultiplier, atmosphereIntensity, windStrength);
        PortalWorldResources.Track(_dreamGo);
        if (_characterGo != null)
        {
            MaterialMapper.ApplyPortalTarget(_characterGo, portalTargetMaterial, useStencil, clipPlane, useClip, lightMultiplier, atmosphereIntensity, windStrength);
        }
        if (_outsideFloorGo != null)
        {
            MaterialMapper.ApplyPortalTarget(_outsideFloorGo, portalTargetMaterial, false, Vector4.zero, false, lightMultiplier * 0.92f, atmosphereIntensity * 0.85f, windStrength);
        }

        UpdatePortalState();
    }

    /// <summary>
    /// 实时同步校准参数、双空间门轴旋转、非均匀缩放补偿与铃芽 20 骨骼/IK 状态。
    /// </summary>
    public void UpdatePortalState()
    {
        float uniformScale = Mathf.Max(0.2f, portalHeight / PortalConfig.BaseDoorHeight);
        transform.position = portalPosition;
        transform.rotation = Quaternion.Euler(0f, portalYaw, 0f);
        float widthScale = portalWidth > 0f ? portalWidth / PortalConfig.BaseDoorWidth : uniformScale;
        transform.localScale = new Vector3(widthScale, uniformScale, uniformScale);
        if (_dreamGo != null)
        {
            float sc = dreamWorldScale > 0f ? dreamWorldScale : PortalConfig.DreamWorldScale;
            // Fit the physical opening without stretching the landscape itself sideways.
            _dreamGo.transform.localScale = new Vector3(sc * uniformScale / widthScale, sc, sc);
            _dreamGo.SetActive(!calibrationHidden);
        }

        bool cameraBehindPortal = false;
        var mainCam = Camera.main;
        if (mainCam != null)
        {
            Vector3 localCam = transform.InverseTransformPoint(mainCam.transform.position);
            cameraBehindPortal = localCam.z <= 0.02f;
        }
        bool effectiveFullMeadow = fullMeadowView || cameraBehindPortal;

        bool useStencil = !effectiveFullMeadow && (Application.isPlaying || !PortalConfig.DisableStencilInEditMode);
        bool useClip = !effectiveFullMeadow;
        Vector4 otherworldClipPlane = ComputeWorldClipPlane();
        // 庭院侧半平面（法线指向门外 +Z，与异世界半平面严格互补）
        Vector4 courtyardClipPlane = -otherworldClipPlane;

        if (_maskGo != null)
        {
            _maskGo.SetActive(!effectiveFullMeadow && !calibrationHidden);
        }

        if (_doorGo != null)
        {
            _doorGo.SetActive(!fullMeadowView && !calibrationHidden && frameMode != PortalConfig.FrameMode.Hidden);
            if (_doorGo.activeSelf)
            {
                MaterialMapper.ApplyDoorMaterials(_doorGo, frameMode);
            }
        }

        if (_rigidHingeCompGo != null)
        {
            bool leafActive = !fullMeadowView && showDoorLeaf && !calibrationHidden && frameMode != PortalConfig.FrameMode.Hidden;
            _rigidHingeCompGo.SetActive(leafActive);
            if (leafActive)
            {
                // makeDoorLeafRigid32：若父级存在非均匀 X 缩放，先在补偿层抵消，防止旋转门扇时产生斜切拉伸
                Vector3 pScale = transform.localScale;
                float ratioX = (Mathf.Abs(pScale.y) > 1e-5f && Mathf.Abs(pScale.x) > 1e-5f)
                    ? Mathf.Abs(pScale.y / pScale.x)
                    : 1f;
                _rigidHingeCompGo.transform.localScale = new Vector3(ratioX, 1f, 1f);

                Quaternion hingeRot = Quaternion.Euler(0f, doorOpenAngle, 0f);
                if (_dayDoorHingeGo != null)
                {
                    _dayDoorHingeGo.transform.localPosition = new Vector3(PortalConfig.DoorHingeX / ratioX, 0f, PortalConfig.DoorHingeZ);
                    _dayDoorHingeGo.transform.localRotation = hingeRot;
                    MaterialMapper.ApplyDoorSpatialMaterials(_dayDoorHingeGo, frameMode, isNightRealmHalf: false, courtyardClipPlane, useClip, useStencil);
                }
                if (_nightDoorHingeGo != null)
                {
                    _nightDoorHingeGo.transform.localPosition = new Vector3(PortalConfig.DoorHingeX / ratioX, 0f, PortalConfig.DoorHingeZ);
                    _nightDoorHingeGo.transform.localRotation = hingeRot;
                    MaterialMapper.ApplyDoorSpatialMaterials(_nightDoorHingeGo, frameMode, isNightRealmHalf: true, otherworldClipPlane, useClip, useStencil);
                }
            }
        }

        if (_characterGo != null)
        {
            _characterGo.SetActive(showCharacter && !calibrationHidden);
            _characterGo.transform.localScale = new Vector3(uniformScale / widthScale, 1f, 1f);
            if (showCharacter)
            {
                if (characterPoseMode == SuzumeRigController.PoseMode.MovieDoorOpening)
                {
                    _characterGo.transform.localPosition = PortalConfig.CharacterDoorPushOffset;
                    _characterGo.transform.localRotation = Quaternion.Euler(0f, PortalConfig.CharacterDoorPushYaw, 0f);
                }
                else
                {
                    _characterGo.transform.localPosition = PortalConfig.CharacterOffset;
                    _characterGo.transform.localRotation = Quaternion.Euler(0f, PortalConfig.CharacterYaw, 0f);
                }

                if (_rigController == null) _rigController = _characterGo.GetComponent<SuzumeRigController>();
                if (_rigController != null)
                {
                    _rigController.poseMode = characterPoseMode;
                    _rigController.headYaw = characterHeadYaw;
                    _rigController.headPitch = characterHeadPitch;
                    _rigController.rightArmLift = characterRightArmLift;
                    _rigController.ApplyPose(_doorKnobTarget, doorOpenAngle);
                }
            }
        }

        if (_outsideFloorGo != null)
        {
            bool isHeadsetDevice = Application.platform == RuntimePlatform.Android && !Application.isEditor;
            bool showFloor = showOutsideReferenceFloor && !effectiveFullMeadow && !isHeadsetDevice && !calibrationHidden;
            _outsideFloorGo.SetActive(showFloor);
            if (showFloor)
            {
                MaterialMapper.UpdatePortalTargetParams(_outsideFloorGo, false, Vector4.zero, false, lightMultiplier * 0.92f, atmosphereIntensity * 0.85f, windStrength);
                int floorStencilComp = useStencil ? 6 : 8; // 6 = NotEqual (禁止门外庭院草坪在门洞 Stencil==1 内部渲染或写入深度)
                foreach (var mr in _outsideFloorGo.GetComponentsInChildren<MeshRenderer>(true))
                {
                    var m = mr.sharedMaterial;
                    if (m != null && m.HasProperty("_StencilComp"))
                    {
                        m.SetInt("_StencilComp", floorStencilComp);
                        m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry - 20;
                    }
                }
            }
        }

        MaterialMapper.UpdatePortalTargetParams(_dreamGo, useStencil, otherworldClipPlane, useClip, lightMultiplier, atmosphereIntensity, windStrength);
        if (_characterGo != null)
        {
            MaterialMapper.UpdatePortalTargetParams(_characterGo, useStencil, otherworldClipPlane, useClip, lightMultiplier, atmosphereIntensity, windStrength);
        }
    }

    /// <summary>
    /// 计算世界空间中的门洞裁剪平面（法线指向门内 -Z，即 -transform.forward），
    /// 使得门洞平面后方（门内花海，dot(worldPos, n) + d >= 0）保留，门前（观察者侧）被 clip 丢弃。
    /// </summary>
    public Vector4 ComputeWorldClipPlane()
    {
        Vector3 normalIntoPortal = -transform.forward.normalized;
        Vector3 planePoint = transform.position + normalIntoPortal * 0.005f;
        float d = -Vector3.Dot(normalIntoPortal, planePoint);
        return new Vector4(normalIntoPortal.x, normalIntoPortal.y, normalIntoPortal.z, d);
    }

    void BuildDreamWorld()
    {
        var prefab = mountainLandscape ? Resources.Load<GameObject>("Worlds/MountainWorld") : dreamWorldPrefab;
        if (prefab == null && mountainLandscape) { mountainLandscape = false; prefab = dreamWorldPrefab; }
        _dreamGo = prefab != null ? Instantiate(prefab) : DreamWorldBuilder.Build();
        _dreamGo.name = DreamName;
        _dreamGo.transform.SetParent(transform, false);
        _dreamGo.transform.localPosition = dreamWorldOffset != Vector3.zero ? dreamWorldOffset : PortalConfig.DreamWorldOffset;
        _dreamGo.transform.localRotation = Quaternion.identity;
        _dreamGo.transform.localScale = Vector3.one * (dreamWorldScale > 0f ? dreamWorldScale : PortalConfig.DreamWorldScale);
        DreamWorldAtmosphere.Build(_dreamGo.transform);
        MarkDontSave(_dreamGo);
    }

    public void SetLandscape(bool mountain)
    {
        if (mountainLandscape == mountain) return;
        if (mountain && Resources.Load<GameObject>("Worlds/MountainWorld") == null)
        { Debug.LogError("[PortalWorld] mountain asset missing"); return; }
        mountainLandscape = mountain;
        if (_dreamGo != null)
        {
            var old = _dreamGo; old.SetActive(false); old.transform.SetParent(null);
            if (Application.isPlaying) Destroy(old); else DestroyImmediate(old);
        }
        BuildDreamWorld();
        MaterialMapper.ApplyPortalTarget(_dreamGo, portalTargetMaterial, !fullMeadowView, ComputeWorldClipPlane(), !fullMeadowView, lightMultiplier, atmosphereIntensity, windStrength);
        PortalWorldResources.Track(_dreamGo);
        UpdatePortalState();
        if (Application.isPlaying) { PlayerPrefs.SetInt("SuzumePortal.Landscape", mountain ? 1 : 0); PlayerPrefs.Save(); }
        Debug.Log("[PortalWorld] landscape=" + (mountain ? "mountain" : "flat"));
    }

    // ---------------- 参数持久化 ----------------

    [System.Serializable]
    struct CalibrationData
    {
        public float height;
        public float width;
        public float x, y, z;
        public float yaw;
        public float light;
        public float atmosphere;
        public float wind;
        public int frameMode;
        public bool showLeaf;
        public float leafAngle;
        public bool showChar;
        public int charPoseMode;
    }

    public void SaveCalibration()
    {
        var data = new CalibrationData
        {
            height = portalHeight,
            width = portalWidth,
            x = portalPosition.x,
            y = portalPosition.y,
            z = portalPosition.z,
            yaw = portalYaw,
            light = lightMultiplier,
            atmosphere = atmosphereIntensity,
            wind = windStrength,
            frameMode = (int)frameMode,
            showLeaf = showDoorLeaf,
            leafAngle = doorOpenAngle,
            showChar = showCharacter,
            charPoseMode = (int)characterPoseMode
        };
        PlayerPrefs.SetString(CalibPrefKey, JsonUtility.ToJson(data));
        PlayerPrefs.Save();
    }

    public void RestoreCalibration()
    {
        if (!PlayerPrefs.HasKey(CalibPrefKey)) return;
        var json = PlayerPrefs.GetString(CalibPrefKey);
        var data = JsonUtility.FromJson<CalibrationData>(json);
        portalHeight = data.height > 0.3f ? data.height : PortalConfig.BaseDoorHeight;
        portalWidth = data.width >= .35f ? data.width : 0f;
        portalPosition = new Vector3(data.x, data.y, data.z);
        portalYaw = data.yaw;
        lightMultiplier = data.light > 0.1f ? data.light : PortalConfig.LightMultiplier;
        atmosphereIntensity = data.atmosphere > 0.1f ? data.atmosphere : PortalConfig.AtmosphereIntensity;
        windStrength = data.wind >= 0f ? data.wind : PortalConfig.WindStrength;
        frameMode = (PortalConfig.FrameMode)Mathf.Clamp(data.frameMode, 0, 2);
        showDoorLeaf = data.showLeaf;
        doorOpenAngle = data.leafAngle;
        showCharacter = data.showChar;
        characterPoseMode = (SuzumeRigController.PoseMode)Mathf.Clamp(data.charPoseMode, 0, 1);
        UpdatePortalState();
    }

    public void ResetCalibration()
    {
        portalHeight = PortalConfig.BaseDoorHeight;
        portalWidth = 0f;
        portalPosition = PortalConfig.PortalPosition;
        portalYaw = PortalConfig.PortalRotationY;
        lightMultiplier = PortalConfig.LightMultiplier;
        atmosphereIntensity = PortalConfig.AtmosphereIntensity;
        windStrength = PortalConfig.WindStrength;
        frameMode = PortalConfig.DefaultFrameMode;
        showDoorLeaf = PortalConfig.DefaultShowDoorLeaf;
        doorOpenAngle = PortalConfig.DoorOpenAngle;
        targetDoorOpen = true;
        animateDoorSmoothly = false;
        showCharacter = PortalConfig.UseCharacter;
        characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;
        characterHeadYaw = 0f;
        characterHeadPitch = 0f;
        characterRightArmLift = 0f;
        fullMeadowView = false;
        UpdatePortalState();
    }

    // ---------------- 门洞遮罩与外部参考地面 ----------------

    void OpenUpDoorway(GameObject doorRoot)
    {
        string[] hideKeys = { "可开合门扇", "空间门洞传送门开口", "PortalAperture" };
        foreach (var r in doorRoot.GetComponentsInChildren<Renderer>(true))
        {
            foreach (var k in hideKeys)
            {
                if (r.gameObject.name.Contains(k))
                {
                    r.enabled = false;
                    foreach (var sub in r.GetComponentsInChildren<Renderer>(true))
                        sub.enabled = false;
                    break;
                }
            }
        }
    }

    GameObject BuildMask()
    {
        var mask = GameObject.CreatePrimitive(PrimitiveType.Quad);
        mask.name = MaskName;
        mask.transform.SetParent(transform, false);

        float w = PortalConfig.BaseDoorWidth;
        float h = PortalConfig.BaseDoorHeight;
        float cy = PortalConfig.OpeningCenterY;

        mask.transform.localScale = new Vector3(w, h, 1f);
        mask.transform.localPosition = new Vector3(0f, cy, 0f);
        mask.transform.localRotation = Quaternion.identity;

        var mr = mask.GetComponent<MeshRenderer>();
        mr.sharedMaterial = portalMaskMaterial != null ? portalMaskMaterial : MakeFallback("Suzume/PortalMask");
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        mr.receiveShadows = false;
        StripCollider(mask);
        return mask;
    }

    GameObject BuildOutsideReferenceFloor()
    {
        var root = new GameObject(OutsideFloorName);
        root.transform.SetParent(transform, false);
        root.transform.localPosition = Vector3.zero;

        // 门外庭院连续草坪基底（由 Stencil NotEqual 1 自动避开门洞内部，向左右地平线自然延展）
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "OutsideFloorPlane";
        floor.transform.SetParent(root.transform, false);
        floor.transform.localPosition = new Vector3(0f, -0.025f, 0f);
        floor.transform.localScale = new Vector3(8f, 1f, 8f);
        StripCollider(floor);

        // 在门框四周庭院生成 12,000 株随风摆动的三维青草草叶，彻底告别方格网
        DreamWorldAtmosphere.BuildCourtyardGrassPatch(root.transform, 12000);

        return root;
    }

    void Clear()
    {
        for (int i = transform.childCount - 1; i >= 0; i--)
        {
            var c = transform.GetChild(i).gameObject;
            if (Application.isPlaying) { c.SetActive(false); c.transform.SetParent(null); Destroy(c); }
            else DestroyImmediate(c);
        }
        _maskGo = null;
        _dreamGo = null;
        _characterGo = null;
        _rigController = null;
        _doorGo = null;
        _rigidHingeCompGo = null;
        _dayDoorHingeGo = null;
        _nightDoorHingeGo = null;
        _doorKnobTarget = null;
        _outsideFloorGo = null;
    }

    void MarkDontSave(GameObject go)
    {
        if (go == null || Application.isPlaying) return;
        foreach (var t in go.GetComponentsInChildren<Transform>(true))
            t.gameObject.hideFlags = HideFlags.DontSave;
    }

    static void StripCollider(GameObject go)
    {
        var col = go.GetComponent<Collider>();
        if (col == null) return;
        if (Application.isPlaying) Destroy(col); else DestroyImmediate(col);
    }

    static Material MakeFallback(string shaderName)
    {
        var sh = Shader.Find(shaderName) ?? Shader.Find("Standard");
        return new Material(sh) { hideFlags = HideFlags.DontSave };
    }
}
