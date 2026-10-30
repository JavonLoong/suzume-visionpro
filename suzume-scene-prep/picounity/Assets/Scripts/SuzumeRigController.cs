using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 铃芽（Suzume）20 骨骼节点绑定与旋转控制器（对应 rig_character.py / fit_pose_v16.py / integrate_door_v32.py）：
/// 1. 自动绑定 Character.fbx 内的 SuzumeHunyuanRig 20 根骨骼节点：
///    - 躯干主链：root -> pelvis -> spine -> chest -> neck -> head
///    - 左臂链：upper_arm.L -> forearm.L -> hand.L -> fingers.L
///    - 右臂链：upper_arm.R -> forearm.R -> hand.R -> fingers.R
///    - 左腿链：thigh.L -> shin.L -> foot.L
///    - 右腿链：thigh.R -> shin.R -> foot.R
/// 2. 支持两种姿态模式：
///    - MeadowLookout（默认花海远眺站姿）：站在门后 2.7m 处望向星空花海，支持头部偏航/俯仰与右臂抬起旋转调节；
///    - MovieDoorOpening（v32/v37 电影推门姿态）：站在门槛处，右手通过余弦定理二连杆解析 IK（SolveTwoBoneIK）实时跟随旋转门扇上的门把手（DoorKnobTarget）！
/// </summary>
[ExecuteAlways]
public class SuzumeRigController : MonoBehaviour
{
    public enum PoseMode
    {
        MeadowLookout = 0,     // 门后 2.7m 花海远眺站姿
        MovieDoorOpening = 1   // 电影门槛右手推门联动姿态（v32/v37 二连杆 IK）
    }

    public static readonly string[] RequiredBoneNames = new string[]
    {
        "root", "pelvis", "spine", "chest", "neck", "head",
        "upper_arm.L", "forearm.L", "hand.L", "fingers.L",
        "upper_arm.R", "forearm.R", "hand.R", "fingers.R",
        "thigh.L", "shin.L", "foot.L",
        "thigh.R", "shin.R", "foot.R"
    };

    [Header("姿态模式")]
    public PoseMode poseMode = PoseMode.MeadowLookout;

    [Header("骨骼旋转微调（度）")]
    [Range(-45f, 45f)]
    public float headYaw = 0f;
    [Range(-30f, 30f)]
    public float headPitch = 0f;
    [Range(-30f, 90f)]
    public float rightArmLift = 0f;

    [Header("电影推门 IK 目标（门扇把手节点）")]
    public Transform doorKnobTarget;

    [Header("已绑定的 20 骨骼节点引用")]
    public Transform rigRoot;
    public List<Transform> boundBones = new List<Transform>();

    readonly Dictionary<string, Transform> _boneMap = new Dictionary<string, Transform>();
    readonly Dictionary<string, Quaternion> _restLocalRot = new Dictionary<string, Quaternion>();
    readonly Dictionary<string, Vector3> _restLocalPos = new Dictionary<string, Vector3>();
    bool _initialized;

    public int BoundBoneCount => _boneMap.Count;

    void OnEnable()
    {
        EnsureBound();
    }

    /// <summary>
    /// 扫描并绑定 Character.fbx 中的 SuzumeHunyuanRig 20 根骨骼节点，记录初始静息姿态（Rest Pose）。
    /// </summary>
    public bool EnsureBound()
    {
        if (_initialized && _boneMap.Count == RequiredBoneNames.Length) return true;

        _boneMap.Clear();
        _restLocalRot.Clear();
        _restLocalPos.Clear();
        boundBones.Clear();

        foreach (var t in GetComponentsInChildren<Transform>(true))
        {
            if (t.name == "SuzumeHunyuanRig")
            {
                rigRoot = t;
            }
        }

        Transform searchRoot = rigRoot != null ? rigRoot : transform;
        foreach (var t in searchRoot.GetComponentsInChildren<Transform>(true))
        {
            foreach (var boneName in RequiredBoneNames)
            {
                if (t.name == boneName && !_boneMap.ContainsKey(boneName))
                {
                    _boneMap[boneName] = t;
                    _restLocalRot[boneName] = t.localRotation;
                    _restLocalPos[boneName] = t.localPosition;
                    boundBones.Add(t);
                }
            }
        }

        _initialized = _boneMap.Count > 0;
        return _boneMap.Count == RequiredBoneNames.Length;
    }

    public Transform GetBone(string boneName)
    {
        EnsureBound();
        return _boneMap.TryGetValue(boneName, out var b) ? b : null;
    }

    /// <summary>
    /// 将全部 20 根骨骼恢复为静息姿态（Rest Pose）。
    /// </summary>
    public void ResetToRestPose()
    {
        if (!EnsureBound()) return;
        foreach (var kv in _boneMap)
        {
            if (kv.Value == null) continue;
            kv.Value.localRotation = _restLocalRot[kv.Key];
            kv.Value.localPosition = _restLocalPos[kv.Key];
        }
    }

    /// <summary>
    /// 每帧更新骨骼旋转与二连杆解析 IK。
    /// </summary>
    public void ApplyPose(Transform knobTarget, float doorOpenAngleDeg)
    {
        if (!EnsureBound()) return;
        doorKnobTarget = knobTarget;

        // 1. 先恢复静息骨骼旋转，确保无累积误差
        ResetToRestPose();

        // 2. 模式 A：花海远眺站姿（支持手动旋转头部、胸腔与手臂骨骼）
        if (poseMode == PoseMode.MeadowLookout)
        {
            RotateBoneWorld("head", transform.up, headYaw);
            RotateBoneWorld("head", transform.right, headPitch);
            if (Mathf.Abs(rightArmLift) > 0.01f)
            {
                RotateBoneWorld("upper_arm.R", transform.right, -rightArmLift * 0.65f);
                RotateBoneWorld("forearm.R", transform.right, -rightArmLift * 0.35f);
            }
            return;
        }

        // 3. 模式 B：v32/v37 电影门槛推门姿态（前倾躯干 + 前迈步态 + 右手二连杆解析 IK 握持门把跟随旋转）
        float openT = Mathf.Clamp01(doorOpenAngleDeg / 88.8f);
        Vector3 charRight = transform.right;
        Vector3 charForward = transform.forward;
        Vector3 charUp = transform.up;

        // 躯干微前倾（fit_pose_v16.py 的 torso forward lean）
        RotateBoneWorld("pelvis", charRight, 6f);
        RotateBoneWorld("spine", charRight, 5f);
        RotateBoneWorld("chest", charRight, 6f + 4f * openT);
        RotateBoneWorld("neck", charRight, -8f);
        RotateBoneWorld("head", charRight, -5f + headPitch);
        RotateBoneWorld("head", charUp, headYaw);

        // 左臂自然微摆平衡
        RotateBoneWorld("upper_arm.L", charRight, 14f);
        RotateBoneWorld("upper_arm.L", charForward, 8f);
        RotateBoneWorld("forearm.L", charRight, -18f);

        // 双腿前迈跨槛步态（使用 solve_knee 二连杆解析 IK，右脚在前跨入异世界，左脚在后）
        if (_boneMap.TryGetValue("thigh.R", out var thighR) &&
            _boneMap.TryGetValue("shin.R", out var shinR) &&
            _boneMap.TryGetValue("foot.R", out var footR))
        {
            Vector3 ankleGoalR = footR.position + charForward * 0.14f + charUp * 0.03f;
            SolveTwoBoneIK(thighR, shinR, footR, ankleGoalR, charForward + charUp * 0.1f);
        }
        if (_boneMap.TryGetValue("thigh.L", out var thighL) &&
            _boneMap.TryGetValue("shin.L", out var shinL) &&
            _boneMap.TryGetValue("foot.L", out var footL))
        {
            Vector3 ankleGoalL = footL.position - charForward * 0.12f + charUp * 0.01f;
            SolveTwoBoneIK(thighL, shinL, footL, ankleGoalL, charForward + charUp * 0.1f);
        }

        // 右臂（upper_arm.R -> forearm.R -> hand.R -> fingers.R）通过余弦定理二连杆 IK 实时追踪门把手
        if (_boneMap.TryGetValue("upper_arm.R", out var upperR) &&
            _boneMap.TryGetValue("forearm.R", out var forearmR) &&
            _boneMap.TryGetValue("hand.R", out var handR))
        {
            Vector3 targetWorld = knobTarget != null
                ? knobTarget.position
                : upperR.position + charForward * 0.36f + charUp * 0.04f;

            // 肘部极向量：朝角色右下方与后方自然弯曲
            Vector3 elbowPole = (-charForward * 0.7f + charRight * 0.5f - charUp * 0.4f).normalized;
            SolveTwoBoneIK(upperR, forearmR, handR, targetWorld, elbowPole);

            // 手掌与手指朝向门把微扣
            RotateBoneWorld("hand.R", charRight, -15f);
            RotateBoneWorld("fingers.R", charRight, -25f);
        }
    }

    void RotateBoneWorld(string name, Vector3 worldAxis, float angleDeg)
    {
        if (Mathf.Abs(angleDeg) < 0.001f) return;
        if (_boneMap.TryGetValue(name, out var bone) && bone != null)
        {
            bone.rotation = Quaternion.AngleAxis(angleDeg, worldAxis) * bone.rotation;
        }
    }

    /// <summary>
    /// 余弦定理二连杆解析 IK 求解器（与 fit_pose_v16.py 的 solve_knee 及 integrate_door_v32.py 的右臂求解完全同构）：
    /// 给定根关节 rootBone (a)、中关节 midBone (b)、末端关节 endBone (c) 与目标点 targetWorld，
    /// 精确计算中关节位置并旋转 rootBone 与 midBone，使 endBone 对齐到目标方向与可达距离。
    /// </summary>
    public static void SolveTwoBoneIK(
        Transform rootBone,
        Transform midBone,
        Transform endBone,
        Vector3 targetWorld,
        Vector3 poleWorldDir)
    {
        if (rootBone == null || midBone == null || endBone == null) return;

        Vector3 a = rootBone.position;
        Vector3 b = midBone.position;
        Vector3 c = endBone.position;

        float l1 = Vector3.Distance(a, b);
        float l2 = Vector3.Distance(b, c);
        if (l1 < 1e-4f || l2 < 1e-4f) return;

        Vector3 toTarget = targetWorld - a;
        float rawDist = toTarget.magnitude;
        if (rawDist < 1e-4f) return;

        float minReach = Mathf.Abs(l1 - l2) + 0.002f;
        float maxReach = (l1 + l2) * 0.996f;
        float d = Mathf.Clamp(rawDist, minReach, maxReach);

        Vector3 axis = toTarget / rawDist;
        Vector3 pole = poleWorldDir - axis * Vector3.Dot(poleWorldDir, axis);
        if (pole.sqrMagnitude < 1e-6f)
        {
            pole = Vector3.Cross(axis, Vector3.up);
        }
        pole.Normalize();

        // 余弦定理：along = (d^2 + l1^2 - l2^2) / (2d), h = sqrt(l1^2 - along^2)
        float along = (d * d + l1 * l1 - l2 * l2) / (2f * d);
        float h = Mathf.Sqrt(Mathf.Max(0f, l1 * l1 - along * along));

        Vector3 newMid = a + axis * along + pole * h;
        Vector3 newEnd = a + axis * d;

        // 第一段旋转：将 (b - a) 旋转对齐到 (newMid - a)
        Vector3 curVec1 = b - a;
        Vector3 tgtVec1 = newMid - a;
        if (curVec1.sqrMagnitude > 1e-6f && tgtVec1.sqrMagnitude > 1e-6f)
        {
            rootBone.rotation = Quaternion.FromToRotation(curVec1.normalized, tgtVec1.normalized) * rootBone.rotation;
        }

        // 第二段旋转：读取更新后的中关节与末端位置，将 (c' - b') 旋转对齐到 (newEnd - b')
        Vector3 b2 = midBone.position;
        Vector3 c2 = endBone.position;
        Vector3 curVec2 = c2 - b2;
        Vector3 tgtVec2 = newEnd - b2;
        if (curVec2.sqrMagnitude > 1e-6f && tgtVec2.sqrMagnitude > 1e-6f)
        {
            midBone.rotation = Quaternion.FromToRotation(curVec2.normalized, tgtVec2.normalized) * midBone.rotation;
        }
    }
}
