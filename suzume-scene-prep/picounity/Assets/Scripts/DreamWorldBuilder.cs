using UnityEngine;

/// 门后梦幻世界：星空、水面、花海、柔和的光（程序化占位）。
/// 之后可整体替换为从 Blender 导出的 GLB/FBX 资产（见 USDZ/GLB 导出说明）。
public static class DreamWorldBuilder
{
    public static GameObject Build()
    {
        var world = new GameObject("DreamWorld");

        if (PortalConfig.EnableStars) world.AddChild(BuildStarField());
        if (PortalConfig.EnableWater) world.AddChild(BuildWater());
        if (PortalConfig.EnableFlowerField) world.AddChild(BuildFlowerField());
        world.AddChild(BuildBackdrop());   // 夜空底色，避免门洞内是空的
        world.AddChild(BuildLight());

        return world;
    }

    /// 门后远景：一块大的夜空背景板，让门洞内始终有底色。
    static GameObject BuildBackdrop()
    {
        // Quad 的正面法线朝 -Z；相机在 +Z 侧，所以要转 180° 才不会被背面剔除。
        var bg = GameObject.CreatePrimitive(PrimitiveType.Quad);
        bg.name = "NightBackdrop";
        bg.transform.localPosition = new Vector3(0f, 3f, -12f);
        bg.transform.localScale = new Vector3(30f, 16f, 1f);
        bg.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
        var mat = new Material(Shader.Find("Unlit/Color"));
        mat.color = new Color(0.05f, 0.07f, 0.20f); // 深蓝夜空
        bg.GetComponent<MeshRenderer>().sharedMaterial = mat;
        bg.GetComponent<Collider>().enabled = false;
        return bg;
    }

    static GameObject BuildStarField()
    {
        var stars = new GameObject("Stars");
        var mat = new Material(Shader.Find("Unlit/Color"));
        mat.color = Color.white;

        for (int i = 0; i < 400; i++)
        {
            var s = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            s.name = "Star";
            s.transform.SetParent(stars.transform, false);
            s.transform.localPosition = new Vector3(
                Random.Range(-4f, 4f), Random.Range(0.5f, 5f), Random.Range(-11f, -3f));
            s.transform.localScale = Vector3.one * Random.Range(0.02f, 0.05f);
            s.GetComponent<MeshRenderer>().sharedMaterial = mat;
            s.GetComponent<Collider>().enabled = false;
        }
        return stars;
    }

    static GameObject BuildWater()
    {
        // 注意：Unity 的 Plane 基元是 10x10 米，scale 1.0 = 10m。
        // 位置要让「前边缘」落在门与预览墙之间（世界 z ∈ (0.66, 1.15) 附近），
        // 既能在门洞里看到，又不会穿过墙漏到门外。
        var water = GameObject.CreatePrimitive(PrimitiveType.Plane);
        water.name = "Water";
        water.transform.localPosition = new Vector3(0f, 0.02f, -5.6f);
        water.transform.localScale = new Vector3(1.0f, 1f, 1.0f);   // 10m x 10m
        var mat = new Material(Shader.Find("Standard"));
        mat.color = new Color(0.35f, 0.6f, 0.7f, 0.7f);
        SetupTransparent(mat);
        water.GetComponent<MeshRenderer>().sharedMaterial = mat;
        water.GetComponent<Collider>().enabled = false;
        return water;
    }

    static GameObject BuildFlowerField()
    {
        var field = new GameObject("FlowerField");
        var colors = new[] { Color.magenta, new Color(0.6f, 0.2f, 0.8f), Color.cyan, new Color(1f, 0.6f, 0.2f) };
        for (int i = 0; i < 120; i++)
        {
            var p = GameObject.CreatePrimitive(PrimitiveType.Plane);
            p.name = "FlowerPatch";
            p.transform.SetParent(field.transform, false);
            p.transform.localPosition = new Vector3(
                Random.Range(-4f, 4f), 0.06f, Random.Range(-7f, -1.5f));
            p.transform.localScale = new Vector3(0.02f, 1f, 0.02f);  // Plane 基础 10x10 → 0.2m
            var mat = new Material(Shader.Find("Standard"));
            mat.color = colors[Random.Range(0, colors.Length)];
            p.GetComponent<MeshRenderer>().sharedMaterial = mat;
            p.GetComponent<Collider>().enabled = false;
        }
        return field;
    }

    static GameObject BuildLight()
    {
        var light = new GameObject("Ambient");
        var l = light.AddComponent<Light>();
        l.type = LightType.Point;
        l.color = Color.white;
        l.intensity = 1.5f;
        light.transform.localPosition = new Vector3(0, 3, -3);
        return light;
    }

    static void SetupTransparent(Material mat)
    {
        mat.SetFloat("_Mode", 3);
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;
    }
}

static class GameObjectExtensions
{
    public static void AddChild(this GameObject parent, GameObject child)
    {
        child.transform.SetParent(parent.transform, false);
    }
}
