using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// 用 PICO 4 Ultra 右手柄模型，按真实动作把整段走完并录成视频：
/// 瞄准四个内角并扣扳机，再扣握把推开双世界的门，最后头显走进门里回头。
/// </summary>
public static class FlowSim
{
    const string FrameDir = "D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/picounity/preview/flowsim";
    const string ControllerPath = "Packages/com.unity.xr.picoxr/Assets/Resources/Controller/PICO 4U R.prefab";
    const float Fps = 12f;
    const float Duration = 16.5f;

    static readonly Vector3[] Corners =
    {
        new Vector3(0.42f, 0.08f, 0.28f),
        new Vector3(-0.42f, 0.08f, 0.28f),
        new Vector3(0.42f, 1.95f, 0.28f),
        new Vector3(-0.42f, 1.95f, 0.28f)
    };

    public static void Run()
    {
        if (Directory.Exists(FrameDir)) Directory.Delete(FrameDir, true);
        Directory.CreateDirectory(FrameDir);

        SceneBootstrap.BuildScene();
        var mgr = Object.FindObjectOfType<PortalManager>();
        if (mgr == null)
        {
            Debug.LogError("FlowSim: 没有门");
            EditorApplication.Exit(1);
            return;
        }
        mgr.EnsureBuilt();
        mgr.fullMeadowView = false;
        mgr.frameMode = PortalConfig.FrameMode.Reference;
        mgr.showDoorLeaf = true;
        mgr.showCharacter = true;
        mgr.characterPoseMode = SuzumeRigController.PoseMode.MeadowLookout;
        mgr.doorOpenAngle = 0f;
        mgr.showOutsideReferenceFloor = true;

        var cam = Camera.main;
        if (cam == null)
        {
            var go = new GameObject("FlowCam");
            cam = go.AddComponent<Camera>();
            go.tag = "MainCamera";
        }
        cam.fieldOfView = 58f;
        cam.nearClipPlane = 0.04f;
        cam.farClipPlane = 1200f;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.07f, 0.09f, 0.09f, 1f);

        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ControllerPath);
        if (prefab == null)
        {
            Debug.LogError("FlowSim: 找不到 PICO 4 Ultra 右手柄");
            EditorApplication.Exit(1);
            return;
        }
        var hand = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        hand.name = "PicoRightHand";
        Vector3 tipLocal = FindTip(hand);
        float modelSize = RendererSize(hand);
        float handScale = Mathf.Clamp(0.22f / Mathf.Max(modelSize, 0.001f), 0.4f, 25f);
        hand.transform.localScale = Vector3.one * handScale;
        var showMat = new Material(Shader.Find("Standard"));
        showMat.color = new Color(0.12f, 0.12f, 0.13f);
        showMat.SetFloat("_Glossiness", 0.35f);
        foreach (var renderer in hand.GetComponentsInChildren<Renderer>(true))
        {
            renderer.enabled = true;
            var slots = renderer.sharedMaterials;
            for (int i = 0; i < slots.Length; i++) slots[i] = showMat;
            renderer.sharedMaterials = slots;
        }
        var aimBall = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        aimBall.name = "AimPoint";
        aimBall.transform.localScale = Vector3.one * 0.035f;
        Object.DestroyImmediate(aimBall.GetComponent<Collider>());
        var aimMat = new Material(Shader.Find("Standard"));
        aimMat.color = new Color(1f, 0.75f, 0.1f);
        aimMat.EnableKeyword("_EMISSION");
        aimMat.SetColor("_EmissionColor", new Color(1f, 0.6f, 0.05f));
        aimBall.GetComponent<Renderer>().sharedMaterial = aimMat;
        Transform triggerBone = FindBone(hand.transform, "trigger");
        Quaternion triggerRest = triggerBone != null ? triggerBone.localRotation : Quaternion.identity;

        var marks = new GameObject[4];
        var colors = new[]
        {
            new Color(1f, 0.85f, 0.2f),
            new Color(0.3f, 0.9f, 1f),
            new Color(0.45f, 1f, 0.5f),
            new Color(1f, 0.45f, 0.75f)
        };
        for (int i = 0; i < 4; i++)
        {
            marks[i] = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            marks[i].transform.localScale = Vector3.one * 0.045f;
            Object.DestroyImmediate(marks[i].GetComponent<Collider>());
            var mat = new Material(Shader.Find("Standard"));
            mat.color = colors[i];
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", colors[i] * 0.6f);
            marks[i].GetComponent<Renderer>().sharedMaterial = mat;
            marks[i].SetActive(false);
        }

        int frames = Mathf.CeilToInt(Duration * Fps);
        int w = 1280, h = 720;
        var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        rt.Create();
        var tex = new Texture2D(w, h, TextureFormat.RGB24, false);

        for (int f = 0; f < frames; f++)
        {
            float t = f / Fps;
            PoseAt(t, out Vector3 head, out Vector3 look, out Vector3 aim, out bool trigger, out bool grip, out int marked);

            cam.transform.position = head;
            cam.transform.LookAt(look);

            Vector3 fromHand = aim - (head + cam.transform.right * 0.22f + cam.transform.up * -0.28f + cam.transform.forward * 0.25f);
            if (fromHand.sqrMagnitude < 0.0001f) fromHand = cam.transform.forward;
            Quaternion rot = Quaternion.LookRotation(fromHand.normalized, Vector3.up);
            hand.transform.rotation = rot;
            hand.transform.position = aim - rot * (tipLocal * handScale);
            aimBall.transform.position = aim;
            if (triggerBone != null)
                triggerBone.localRotation = trigger ? triggerRest * Quaternion.Euler(-28f, 0f, 0f) : triggerRest;

            for (int i = 0; i < 4; i++)
            {
                marks[i].SetActive(i < marked);
                marks[i].transform.position = Corners[i];
            }

            mgr.doorOpenAngle = grip ? Mathf.Lerp(0f, PortalConfig.MovieDoorOpenAngle, OpenAmount(t)) : 0f;
            mgr.UpdatePortalState();

            cam.targetTexture = rt;
            cam.Render();
            RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            tex.Apply();
            File.WriteAllBytes(FrameDir + "/f_" + f.ToString("0000") + ".png", tex.EncodeToPNG());
        }

        RenderTexture.active = null;
        cam.targetTexture = null;
        rt.Release();
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(tex);
        EditorSceneManager.SaveOpenScenes();
        Debug.Log("FlowSim frames " + frames + " -> " + FrameDir);
    }

    static float OpenAmount(float t)
    {
        float u = Mathf.InverseLerp(6.2f, 8.6f, t);
        u = Mathf.Clamp01(u);
        return u * u * (3f - 2f * u);
    }

    static void PoseAt(float t, out Vector3 head, out Vector3 look, out Vector3 aim, out bool trigger, out bool grip, out int marked)
    {
        Vector3 stand = new Vector3(0.08f, 1.55f, 1.45f);
        Vector3 doorLook = new Vector3(0f, 1.2f, 0f);
        head = stand;
        look = doorLook;
        trigger = false;
        grip = false;
        marked = 0;

        float[] arrive = { 1.0f, 2.3f, 3.8f, 5.2f };
        float[] press = { 1.35f, 2.65f, 4.15f, 5.55f };
        int stage = 0;
        for (int i = 0; i < 4; i++)
        {
            if (t >= press[i]) marked = i + 1;
            if (t >= arrive[i]) stage = i;
        }

        Vector3 hip = stand + new Vector3(0.28f, -0.35f, -0.15f);
        if (t < 5.9f)
        {
            float segStart = stage == 0 ? 0.15f : press[stage - 1];
            float u = Smooth(Mathf.InverseLerp(segStart, arrive[stage], t));
            Vector3 from = stage == 0 ? hip : Corners[stage - 1];
            aim = Vector3.Lerp(from, Corners[stage], u);
            trigger = t >= arrive[stage] && t < press[stage];
        }
        else if (t < 9.2f)
        {
            float u = Smooth(Mathf.InverseLerp(5.9f, 6.5f, t));
            aim = Vector3.Lerp(Corners[3], hip, u);
            grip = t >= 6.15f;
            marked = 4;
            look = new Vector3(0f, 1.15f, -0.6f);
        }
        else
        {
            marked = 4;
            grip = true;
            aim = hip;
            float u = Smooth(Mathf.InverseLerp(9.2f, 13.2f, t));
            head = Vector3.Lerp(stand, new Vector3(0.05f, 1.62f, -1.7f), u);
            if (t < 13.4f)
                look = new Vector3(0f, 1.15f, -6f);
            else
            {
                float back = Smooth(Mathf.InverseLerp(13.4f, 15.4f, t));
                look = Vector3.Lerp(new Vector3(0f, 1.15f, -6f), new Vector3(0f, 1.35f, 0.4f), back);
                head = Vector3.Lerp(new Vector3(0.05f, 1.62f, -1.7f), new Vector3(-0.35f, 1.6f, -2.3f), back);
            }
            aim = head + new Vector3(0.22f, -0.42f, 0.05f);
        }
    }

    static float Smooth(float u)
    {
        u = Mathf.Clamp01(u);
        return u * u * (3f - 2f * u);
    }

    static float RendererSize(GameObject hand)
    {
        bool any = false;
        Bounds bounds = new Bounds(hand.transform.position, Vector3.zero);
        foreach (var renderer in hand.GetComponentsInChildren<Renderer>(true))
        {
            if (!any)
            {
                bounds = renderer.bounds;
                any = true;
            }
            else bounds.Encapsulate(renderer.bounds);
        }
        if (!any) return 0.05f;
        return Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z);
    }

    static float TipBoundsSize(GameObject hand)
    {
        bool any = false;
        Bounds bounds = new Bounds(Vector3.zero, Vector3.zero);
        foreach (var filter in hand.GetComponentsInChildren<MeshFilter>(true))
        {
            if (filter.sharedMesh == null) continue;
            foreach (var vertex in filter.sharedMesh.vertices)
            {
                Vector3 point = hand.transform.InverseTransformPoint(filter.transform.TransformPoint(vertex));
                if (!any) { bounds = new Bounds(point, Vector3.zero); any = true; }
                else bounds.Encapsulate(point);
            }
        }
        foreach (var skin in hand.GetComponentsInChildren<SkinnedMeshRenderer>(true))
        {
            if (skin.sharedMesh == null) continue;
            foreach (var vertex in skin.sharedMesh.vertices)
            {
                Vector3 point = hand.transform.InverseTransformPoint(skin.transform.TransformPoint(vertex));
                if (!any) { bounds = new Bounds(point, Vector3.zero); any = true; }
                else bounds.Encapsulate(point);
            }
        }
        return any ? Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z) : 0.01f;
    }

    static Transform FindBone(Transform root, string token)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
        {
            if (t.name.ToLowerInvariant().Contains(token))
                return t;
        }
        return null;
    }

    static Vector3 FindTip(GameObject hand)
    {
        bool any = false;
        Bounds bounds = new Bounds(Vector3.zero, Vector3.zero);
        foreach (var filter in hand.GetComponentsInChildren<MeshFilter>())
        {
            if (filter.sharedMesh == null) continue;
            foreach (var vertex in filter.sharedMesh.vertices)
            {
                Vector3 point = hand.transform.InverseTransformPoint(filter.transform.TransformPoint(vertex));
                if (!any)
                {
                    bounds = new Bounds(point, Vector3.zero);
                    any = true;
                }
                else bounds.Encapsulate(point);
            }
        }
        foreach (var skin in hand.GetComponentsInChildren<SkinnedMeshRenderer>())
        {
            if (skin.sharedMesh == null) continue;
            foreach (var vertex in skin.sharedMesh.vertices)
            {
                Vector3 point = hand.transform.InverseTransformPoint(skin.transform.TransformPoint(vertex));
                if (!any)
                {
                    bounds = new Bounds(point, Vector3.zero);
                    any = true;
                }
                else bounds.Encapsulate(point);
            }
        }
        if (!any) return Vector3.forward * 0.08f;
        Vector3 center = bounds.center;
        Vector3 best = center;
        float bestDist = 0f;
        foreach (var filter in hand.GetComponentsInChildren<MeshFilter>())
        {
            if (filter.sharedMesh == null) continue;
            foreach (var vertex in filter.sharedMesh.vertices)
            {
                Vector3 point = hand.transform.InverseTransformPoint(filter.transform.TransformPoint(vertex));
                float dist = (point - center).sqrMagnitude;
                if (dist > bestDist)
                {
                    bestDist = dist;
                    best = point;
                }
            }
        }
        foreach (var skin in hand.GetComponentsInChildren<SkinnedMeshRenderer>())
        {
            if (skin.sharedMesh == null) continue;
            foreach (var vertex in skin.sharedMesh.vertices)
            {
                Vector3 point = hand.transform.InverseTransformPoint(skin.transform.TransformPoint(vertex));
                float dist = (point - center).sqrMagnitude;
                if (dist > bestDist)
                {
                    bestDist = dist;
                    best = point;
                }
            }
        }
        return best;
    }
}
