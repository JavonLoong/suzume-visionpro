using UnityEngine;

/// <summary>
/// 铃芽之旅 · 梦幻门运行时视角控制、双空间门轴旋转与 20 骨骼姿态面板：
/// - 支持鼠标拖拽 / 滚轮 / 滑块调整观察者相对门洞的左右位置、眼睛高度、距门距离，直观验证门洞视差；
/// - 支持一键切换「门洞预览」与「查看完整花海」；
/// - 支持双空间刚性门扇的一键平滑「开门 (88.8°)」/「关门 (0°)」以及任意角度滑块；
/// - 支持铃芽角色 20 骨骼系统的「花海远眺站姿 (2.7m)」与「电影门槛推门联动 (二连杆 IK)」切换及骨骼旋转滑块；
/// - 按 Tab 或 H 键可随时隐藏/呼出右侧控制面板。
/// </summary>
public class PortalCalibrationUI : MonoBehaviour
{
    public PortalManager portalManager;
    public Camera targetCamera;

    [Header("观察相机姿态（米）")]
    [Range(-1.8f, 1.8f)]
    public float cameraX = 0f;
    [Range(0.6f, 2.5f)]
    public float cameraY = 1.60f;
    [Range(0.65f, 6.0f)]
    public float cameraZ = 3.20f;

    [Header("UI 显示控制")]
    public bool showUI = true;

    bool _dragging;
    Vector3 _dragStartMouse;
    float _dragStartX;
    float _dragStartY;

    GUIStyle _panelStyle;
    GUIStyle _titleStyle;
    GUIStyle _subTitleStyle;
    GUIStyle _labelStyle;
    GUIStyle _buttonStyle;
    Texture2D _panelTex;

    void Start()
    {
        if (portalManager == null) portalManager = FindObjectOfType<PortalManager>();
        if (targetCamera == null) targetCamera = Camera.main;
        if (!Application.isEditor && Application.platform == RuntimePlatform.Android)
        {
            showUI = false;
            return;
        }
        ApplyCameraPose();
    }

    void Update()
    {
        if (portalManager == null) portalManager = FindObjectOfType<PortalManager>();
        if (targetCamera == null) targetCamera = Camera.main;

        if (Input.GetKeyDown(KeyCode.Tab) || Input.GetKeyDown(KeyCode.H))
        {
            showUI = !showUI;
        }

        bool isDesktopPreview = Application.isEditor || Application.platform != RuntimePlatform.Android;
        if (isDesktopPreview && targetCamera != null)
        {
            float dt = Time.deltaTime > 0f ? Mathf.Min(Time.deltaTime, 0.05f) : 0.016f;

            // 键盘方向键 ← / → 或 Q / E：实时推拉木门旋转（0° ~ 120°）
            float doorDelta = 0f;
            if (Input.GetKey(KeyCode.RightArrow) || Input.GetKey(KeyCode.E)) doorDelta += 55f * dt;
            if (Input.GetKey(KeyCode.LeftArrow) || Input.GetKey(KeyCode.Q)) doorDelta -= 55f * dt;
            if (Mathf.Abs(doorDelta) > 0.001f && portalManager != null)
            {
                portalManager.showDoorLeaf = true;
                portalManager.animateDoorSmoothly = false;
                portalManager.doorOpenAngle = Mathf.Clamp(portalManager.doorOpenAngle + doorDelta, 0f, 120f);
                portalManager.UpdatePortalState();
            }

            // 空格键 Space：一键触发平滑开门 (88.8°) / 平滑关门 (0°)
            if (Input.GetKeyDown(KeyCode.Space) && portalManager != null)
            {
                bool shouldOpen = portalManager.doorOpenAngle < 45f;
                portalManager.ToggleDoorOpen(shouldOpen);
            }

            // 数字键 1 / 2：快捷切换铃芽「花海远眺」与「门槛推门联动 (IK)」姿态
            if (Input.GetKeyDown(KeyCode.Alpha1) && portalManager != null)
            {
                portalManager.showCharacter = true;
                portalManager.characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;
                portalManager.UpdatePortalState();
            }
            if (Input.GetKeyDown(KeyCode.Alpha2) && portalManager != null)
            {
                portalManager.showCharacter = true;
                portalManager.showDoorLeaf = true;
                portalManager.characterPoseMode = SuzumeRigController.PoseMode.MovieDoorOpening;
                portalManager.UpdatePortalState();
            }

            // WASD 键：平滑移动观察者相机视角
            float moveX = 0f, moveZ = 0f;
            if (Input.GetKey(KeyCode.A)) moveX -= 1.2f * dt;
            if (Input.GetKey(KeyCode.D)) moveX += 1.2f * dt;
            if (Input.GetKey(KeyCode.W)) moveZ -= 1.5f * dt;
            if (Input.GetKey(KeyCode.S)) moveZ += 1.5f * dt;
            if (Mathf.Abs(moveX) > 0.0001f || Mathf.Abs(moveZ) > 0.0001f)
            {
                cameraX = Mathf.Clamp(cameraX + moveX, -1.8f, 1.8f);
                cameraZ = Mathf.Clamp(cameraZ + moveZ, 0.65f, 6.0f);
                ApplyCameraPose();
            }

            float panelLeft = showUI ? (Screen.width - 320f) : Screen.width;
            bool mouseInStage = Input.mousePosition.x < panelLeft;

            if (Input.GetMouseButtonDown(0) && mouseInStage)
            {
                _dragging = true;
                _dragStartMouse = Input.mousePosition;
                _dragStartX = cameraX;
                _dragStartY = cameraY;
            }
            if (Input.GetMouseButtonUp(0))
            {
                _dragging = false;
            }
            if (_dragging && Input.GetMouseButton(0))
            {
                Vector3 delta = Input.mousePosition - _dragStartMouse;
                cameraX = Mathf.Clamp(_dragStartX + delta.x * 0.005f, -1.8f, 1.8f);
                cameraY = Mathf.Clamp(_dragStartY - delta.y * 0.004f, 0.6f, 2.5f);
                ApplyCameraPose();
            }

            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) > 0.0001f && mouseInStage)
            {
                cameraZ = Mathf.Clamp(cameraZ - scroll * 1.8f, 0.65f, 6.0f);
                ApplyCameraPose();
            }
        }
    }

    public void ApplyCameraPose()
    {
        if (targetCamera == null) return;
        Vector3 rootPos = portalManager != null ? portalManager.portalPosition : Vector3.zero;
        float scale = portalManager != null ? (portalManager.portalHeight / PortalConfig.BaseDoorHeight) : 1f;

        targetCamera.transform.position = rootPos + new Vector3(cameraX, cameraY * scale, cameraZ);
        bool full = portalManager != null && portalManager.fullMeadowView;
        Vector3 lookTarget = full
            ? rootPos + new Vector3(0f, 0.80f * scale, -8.0f)
            : rootPos + new Vector3(0f, 1.05f * scale, 0f);
        targetCamera.transform.LookAt(lookTarget);
        targetCamera.fieldOfView = PortalConfig.DefaultCameraFov;
        targetCamera.allowMSAA = true;
        targetCamera.allowHDR = true;
        targetCamera.backgroundColor = full
            ? new Color(0.031f, 0.039f, 0.114f, 1f)
            : new Color(0.094f, 0.133f, 0.114f, 1f);
    }

    public void ResetView()
    {
        cameraX = 0f;
        cameraY = 1.60f;
        cameraZ = 3.20f;
        if (portalManager != null)
        {
            portalManager.fullMeadowView = false;
            portalManager.UpdatePortalState();
        }
        ApplyCameraPose();
    }

    void EnsureStyles()
    {
        if (_panelStyle != null) return;

        _panelTex = new Texture2D(1, 1) { hideFlags = HideFlags.DontSave };
        _panelTex.SetPixel(0, 0, new Color(0.10f, 0.15f, 0.13f, 0.92f));
        _panelTex.Apply();

        _panelStyle = new GUIStyle(GUI.skin.box);
        _panelStyle.normal.background = _panelTex;
        _panelStyle.padding = new RectOffset(12, 12, 10, 10);

        _titleStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 15,
            fontStyle = FontStyle.Bold,
            normal = { textColor = new Color(0.88f, 0.94f, 0.87f) }
        };

        _subTitleStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 12,
            fontStyle = FontStyle.Bold,
            normal = { textColor = new Color(0.83f, 0.90f, 0.81f) }
        };

        _labelStyle = new GUIStyle(GUI.skin.label)
        {
            fontSize = 11,
            normal = { textColor = new Color(0.75f, 0.82f, 0.77f) }
        };

        _buttonStyle = new GUIStyle(GUI.skin.button)
        {
            fontSize = 11,
            fixedHeight = 24f
        };
    }

    void OnGUI()
    {
        if (!showUI || portalManager == null) return;
        EnsureStyles();

        int boneCount = portalManager.RigController != null ? portalManager.RigController.BoundBoneCount : 0;
        string modeLegend = portalManager.fullMeadowView
            ? $"门后世界 · 完整几何检查（铃芽已绑 {boneCount} 根骨骼 | 按 Tab 隐藏面板）"
            : $"门外：庭院门轴 / 门内：三维常世星河（←/→ 推门 | 空格 开关门 | 1/2 切姿态 | Tab 隐藏）";
        GUI.Label(new Rect(18f, 12f, 680f, 24f), modeLegend, _subTitleStyle);

        float w = 308f;
        float h = Mathf.Min(Screen.height - 20f, 730f);
        Rect panelRect = new Rect(Screen.width - w - 10f, 10f, w, h);
        GUILayout.BeginArea(panelRect, _panelStyle);

        GUILayout.Label("铃芽之旅 · 节点旋转与门洞校准", _titleStyle);
        float curH = portalManager.portalHeight;
        float curW = curH * (PortalConfig.BaseDoorWidth / PortalConfig.BaseDoorHeight);
        GUILayout.Label($"门洞净高×净宽：{curH:F2}×{curW:F3}m | 门轴：{portalManager.doorOpenAngle:F1}°", _labelStyle);

        GUILayout.Space(4f);
        GUILayout.Label("一、透过门洞 · 移动视角 (鼠标拖拽/WASD)", _subTitleStyle);

        float nx = DrawSlider("左右移动", cameraX, -1.6f, 1.6f, "m");
        float ny = DrawSlider("眼睛高度", cameraY, 0.6f, 2.4f, "m");
        float nz = DrawSlider("距门距离", cameraZ, 0.65f, 6.0f, "m");
        if (!Mathf.Approximately(nx, cameraX) || !Mathf.Approximately(ny, cameraY) || !Mathf.Approximately(nz, cameraZ))
        {
            cameraX = nx; cameraY = ny; cameraZ = nz;
            ApplyCameraPose();
        }

        GUILayout.BeginHorizontal();
        if (GUILayout.Button("回到门前", _buttonStyle)) ResetView();
        string fullLabel = portalManager.fullMeadowView ? "返回门洞预览" : "查看完整花海";
        if (GUILayout.Button(fullLabel, _buttonStyle))
        {
            portalManager.fullMeadowView = !portalManager.fullMeadowView;
            portalManager.UpdatePortalState();
            ApplyCameraPose();
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(6f);
        GUILayout.Label("二、双空间刚性门轴旋转 (←/→ 或 空格)", _subTitleStyle);
        portalManager.showDoorLeaf = GUILayout.Toggle(portalManager.showDoorLeaf, " 启用双空间同步门扇 (庭院+异世界)");
        if (portalManager.showDoorLeaf)
        {
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("平滑开门 (88.8°)", _buttonStyle)) portalManager.ToggleDoorOpen(true);
            if (GUILayout.Button("平滑关门 (0°)", _buttonStyle)) portalManager.ToggleDoorOpen(false);
            GUILayout.EndHorizontal();

            float nextAngle = DrawSlider("门轴转角", portalManager.doorOpenAngle, 0f, 120f, "°");
            if (Mathf.Abs(nextAngle - portalManager.doorOpenAngle) > 0.05f)
            {
                portalManager.animateDoorSmoothly = false;
                portalManager.doorOpenAngle = nextAngle;
            }
        }

        GUILayout.Space(6f);
        GUILayout.Label($"三、铃芽 {boneCount} 骨骼旋转与推门 IK (按 1/2)", _subTitleStyle);
        portalManager.showCharacter = GUILayout.Toggle(portalManager.showCharacter, " 显示铃芽角色");
        if (portalManager.showCharacter)
        {
            string[] poseNames = { "花海远眺 (2.7m)", "门槛推门联动 (IK)" };
            int poseIdx = GUILayout.SelectionGrid((int)portalManager.characterPoseMode, poseNames, 2);
            if (poseIdx != (int)portalManager.characterPoseMode)
            {
                portalManager.characterPoseMode = (SuzumeRigController.PoseMode)poseIdx;
                portalManager.UpdatePortalState();
            }

            portalManager.characterHeadYaw = DrawSlider("头部偏航", portalManager.characterHeadYaw, -40f, 40f, "°");
            portalManager.characterHeadPitch = DrawSlider("头部俯仰", portalManager.characterHeadPitch, -25f, 25f, "°");
            if (portalManager.characterPoseMode == SuzumeRigController.PoseMode.MeadowLookout)
            {
                portalManager.characterRightArmLift = DrawSlider("右臂抬起", portalManager.characterRightArmLift, -20f, 85f, "°");
            }
        }

        GUILayout.Space(6f);
        GUILayout.Label("四、常世奇观与实体门校准", _subTitleStyle);
        portalManager.atmosphereIntensity = DrawSlider("星河奇观", portalManager.atmosphereIntensity, 0.3f, 2.4f, "x");
        portalManager.windStrength = DrawSlider("微风摇曳", portalManager.windStrength, 0f, 2.5f, "x");
        portalManager.lightMultiplier = DrawSlider("花海亮度", portalManager.lightMultiplier, 0.3f, 2.5f, "x");
        portalManager.portalHeight = DrawSlider("门洞净高", portalManager.portalHeight, 0.5f, 3.5f, "m");

        string[] modeNames = { "显示对齐门框", "仅作遮挡", "隐藏门框" };
        int modeIdx = GUILayout.SelectionGrid((int)portalManager.frameMode, modeNames, 3);
        if (modeIdx != (int)portalManager.frameMode)
        {
            portalManager.frameMode = (PortalConfig.FrameMode)modeIdx;
            portalManager.UpdatePortalState();
        }

        GUILayout.Space(4f);
        GUILayout.BeginHorizontal();
        if (GUILayout.Button("保存参数", _buttonStyle)) portalManager.SaveCalibration();
        if (GUILayout.Button("读取参数", _buttonStyle)) { portalManager.RestoreCalibration(); ApplyCameraPose(); }
        if (GUILayout.Button("重置", _buttonStyle)) { portalManager.ResetCalibration(); ResetView(); }
        GUILayout.EndHorizontal();

        GUILayout.EndArea();
    }

    float DrawSlider(string title, float val, float min, float max, string unit)
    {
        GUILayout.BeginHorizontal();
        GUILayout.Label(title, _labelStyle, GUILayout.Width(64f));
        float next = GUILayout.HorizontalSlider(val, min, max);
        GUILayout.Label($"{next:F2} {unit}", _labelStyle, GUILayout.Width(54f));
        GUILayout.EndHorizontal();
        return next;
    }
}
