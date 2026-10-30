using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 材质与烘焙贴图映射器（支持常世星河暮光天幕、发光花海、微风波浪与悬浮星火粒子）：
/// 1. DreamWorld：
///    - DistantSkyMesh -> NightSky.png + _IsSkyDome=1（地平线晚霞 + 斜跨门洞银河拱带 + 3 层闪烁十字星芒）
///    - Geometry_C7FAF2CB_003 (NearMeadow) -> NearMeadow_BaseColor.png + _IsTerrain=1（微风波光 + 远山暮雾融合）
///    - Closed_continuous_far_meadow_v31_001 (DistantMeadow) -> DistantMeadow_BaseColor.png + _IsTerrain=1
///    - Individual_meadow_flowers / ForegroundLuminousFlowers -> FlowerPalette.png + _IsFlower=1（四色星辉荧光 + 顶点微风摇曳）
///    - Modeled_flower_stems / ForegroundFlowerStems -> 翠绿花茎 + _IsGrass=1
///    - Spatial_grass_blades -> 深绿草叶 + _IsGrass=1
///    - FloatingStarlightMotes -> _IsStarMote=1（常世漂浮十字星火微粒）
///    - Solid_native_stars_002 -> 蓝白星辰 HDR 自发光
/// 2. SuzumeCharacter（支持 20 骨骼 SkinnedMeshRenderer）：
///    - node_0 (Body) -> 01_texture_pbr_20250901.png + 05_normal
///    - node_0_001 (Head) -> 02_texture_pbr_20250901_001.png + 06_normal
/// 3. DoorFrame / 双空间同步 DoorLeaf
/// </summary>
public static class MaterialMapper
{
    struct TargetSpec
    {
        public string texName;
        public string normalName;
        public Color baseColor;
        public Color emissionColor;
        public float emissionStrength;
        public bool useTexAsEmission;
        public bool unlit;
        public bool pointFilter;
        public bool isSkyDome;
        public bool isFlower;
        public bool isGrass;
        public bool isTerrain;
        public bool isStarMote;
    }

    static readonly Dictionary<string, Texture2D> TexCache = new Dictionary<string, Texture2D>();

    public static Texture2D LoadTexture(string nameWithoutExt, bool pointFilter = false, bool clamp = false)
    {
        if (string.IsNullOrEmpty(nameWithoutExt)) return null;
        if (TexCache.TryGetValue(nameWithoutExt, out var cached) && cached != null)
        {
            ConfigureTex(cached, pointFilter, clamp);
            return cached;
        }

        var tex = Resources.Load<Texture2D>("Textures/" + nameWithoutExt);
#if UNITY_EDITOR
        if (tex == null)
        {
            tex = UnityEditor.AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Textures/" + nameWithoutExt + ".png")
               ?? UnityEditor.AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Resources/Textures/" + nameWithoutExt + ".png");
        }
#endif
        if (tex != null)
        {
            ConfigureTex(tex, pointFilter, clamp);
            TexCache[nameWithoutExt] = tex;
        }
        else
        {
            Debug.LogWarning("[MaterialMapper] 未找到贴图: " + nameWithoutExt);
        }
        return tex;
    }

    static void ConfigureTex(Texture2D tex, bool pointFilter, bool clamp)
    {
        if (pointFilter)
        {
            tex.filterMode = FilterMode.Point;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.anisoLevel = 1;
        }
        else
        {
            tex.filterMode = FilterMode.Trilinear;
            tex.anisoLevel = 16;
            if (clamp)
            {
                tex.wrapMode = TextureWrapMode.Clamp;
            }
        }
    }

    static bool TryGetTargetSpec(string objName, string matName, out TargetSpec spec)
    {
        spec = new TargetSpec
        {
            baseColor = Color.white,
            emissionColor = Color.black,
            emissionStrength = 0f,
            useTexAsEmission = false,
            unlit = false,
            pointFilter = false,
            isSkyDome = false,
            isFlower = false,
            isGrass = false,
            isTerrain = false,
            isStarMote = false
        };

        string key = objName + "|" + matName;

        // 0. 门内漂浮常世星火微粒
        if (key.Contains("FloatingStarlightMotes"))
        {
            spec.isStarMote = true;
            spec.unlit = true;
            return true;
        }
        // 1. 远景常世暮光星河天幕
        if (key.Contains("DistantSky") || key.Contains("环绕夜空"))
        {
            spec.texName = "NightSky";
            spec.unlit = true;
            spec.isSkyDome = true;
            return true;
        }
        // 2. 近景起伏草原地面 & 门外庭院草坪地面
        if (key.Contains("Geometry_C7FAF2CB") || key.Contains("NearMeadow") || key.Contains("OutsideFloorPlane") || key.Contains("起伏草原地面"))
        {
            spec.texName = "NearMeadow_BaseColor";
            spec.isTerrain = true;
            return true;
        }
        // 3. 远景连续草原
        if (key.Contains("Closed_continuous_far_meadow") || key.Contains("DistantMeadow") || key.Contains("连续远景草原"))
        {
            spec.texName = "DistantMeadow_BaseColor";
            spec.isTerrain = true;
            return true;
        }
        // 4. 门前加密发光花簇（顶点色驱动）
        if (key.Contains("ForegroundLuminousFlowers"))
        {
            spec.isFlower = true;
            spec.useTexAsEmission = true;
            spec.emissionStrength = 0.55f;
            return true;
        }
        // 5. 2500 朵独立花朵（使用调色板最近邻采样 + 荧光提亮）
        if (key.Contains("Individual_meadow_flowers") || key.Contains("FlowerPalette") || key.Contains("草原独立花朵"))
        {
            spec.texName = "FlowerPalette";
            spec.pointFilter = true;
            spec.useTexAsEmission = true;
            spec.emissionStrength = 0.38f;
            spec.isFlower = true;
            return true;
        }
        // 6. 花茎与门前加密花茎
        if (key.Contains("Modeled_flower_stems") || key.Contains("ForegroundFlowerStems") || key.Contains("立体花茎"))
        {
            spec.baseColor = new Color(0.055f, 0.185f, 0.105f, 1f);
            spec.isGrass = true;
            return true;
        }
        // 7. 三维草叶（含门内 18,000 株茂密草丛、门外 5,500 株庭院草丛及原生 5,000 簇草叶）
        if (key.Contains("ForegroundLushGrassBlades") || key.Contains("CourtyardLushGrassBlades") || key.Contains("Spatial_grass_blades") || key.Contains("三维草叶"))
        {
            spec.baseColor = Color.white;
            spec.isGrass = true;
            return true;
        }
        // 8. 立体发光星辰
        if (key.Contains("Solid_native_stars") || key.Contains("Starlight") || key.Contains("立体发光星辰"))
        {
            spec.baseColor = new Color(0.62f, 0.78f, 1.00f, 1f);
            spec.emissionColor = new Color(0.62f, 0.78f, 1.00f, 1f);
            spec.emissionStrength = 3.2f;
            spec.unlit = true;
            return true;
        }
        // 9. 铃芽角色：头部与头发（node_0_001 / Material_002）
        if (key.Contains("node_0_001") || key.Contains("Head") || key.Contains("Material_002"))
        {
            spec.texName = "02_texture_pbr_20250901_001";
            spec.normalName = "06_texture_pbr_20250901_normal_001";
            return true;
        }
        // 10. 铃芽角色：身体与校服（node_0 / Material_001）
        if (key.Contains("node_0") || key.Contains("Body") || key.Contains("Material_001"))
        {
            spec.texName = "01_texture_pbr_20250901";
            spec.normalName = "05_texture_pbr_20250901_normal";
            return true;
        }

        return false;
    }

    public static void Apply(GameObject root, Material targetMat, bool useStencil = true)
    {
        ApplyPortalTarget(root, targetMat, useStencil, new Vector4(0f, 0f, -1f, 0f), useStencil, PortalConfig.LightMultiplier, PortalConfig.AtmosphereIntensity, PortalConfig.WindStrength);
    }

    /// <summary>
    /// 为门后世界（DreamWorld + AtmosphereWonderLayer + Character）应用带 Stencil、门洞裁剪与常世奇观参数的材质。
    /// </summary>
    public static void ApplyPortalTarget(
        GameObject root,
        Material targetMat,
        bool useStencil,
        Vector4 clipPlane,
        bool useClipPlane,
        float lightMultiplier,
        float atmosphereIntensity = 1.35f,
        float windStrength = 1.0f)
    {
        if (root == null) return;

        Shader sh = (targetMat != null && targetMat.shader != null)
            ? targetMat.shader
            : Shader.Find("Suzume/PortalTarget");
        if (sh == null) sh = Shader.Find("Standard");

        int stencilComp = useStencil ? 3 : 8; // 3=Equal, 8=Always

        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
        {
            if (!(r is MeshRenderer || r is SkinnedMeshRenderer)) continue;

            string objName = CleanName(r.gameObject.name);
            string matName = r.sharedMaterial != null ? CleanName(r.sharedMaterial.name) : "";

            var mat = new Material(sh)
            {
                name = "PortalTarget_" + objName,
                hideFlags = HideFlags.DontSave
            };

            if (TryGetTargetSpec(objName, matName, out var spec))
            {
                mat.SetColor("_Color", spec.baseColor);
                mat.color = spec.baseColor;

                if (!string.IsNullOrEmpty(spec.texName))
                {
                    var tex = LoadTexture(spec.texName, spec.pointFilter, spec.texName == "NightSky");
                    if (tex != null) mat.SetTexture("_MainTex", tex);
                }
                if (!string.IsNullOrEmpty(spec.normalName))
                {
                    var norm = LoadTexture(spec.normalName, false, false);
                    if (norm != null)
                    {
                        mat.SetTexture("_BumpMap", norm);
                        mat.SetFloat("_UseNormalMap", 1f);
                    }
                }

                mat.SetColor("_EmissionColor", spec.emissionColor);
                mat.SetFloat("_EmissionStrength", spec.emissionStrength);
                mat.SetFloat("_UseMainTexAsEmission", spec.useTexAsEmission ? 1f : 0f);
                mat.SetFloat("_Unlit", spec.unlit ? 1f : 0f);
                mat.SetFloat("_IsSkyDome", spec.isSkyDome ? 1f : 0f);
                mat.SetFloat("_IsFlower", spec.isFlower ? 1f : 0f);
                mat.SetFloat("_IsGrass", spec.isGrass ? 1f : 0f);
                mat.SetFloat("_IsTerrain", spec.isTerrain ? 1f : 0f);
                mat.SetFloat("_IsStarMote", spec.isStarMote ? 1f : 0f);
            }
            else
            {
                if (r.sharedMaterial != null)
                {
                    if (r.sharedMaterial.HasProperty("_MainTex") && r.sharedMaterial.mainTexture != null)
                        mat.SetTexture("_MainTex", r.sharedMaterial.mainTexture);
                    if (r.sharedMaterial.HasProperty("_Color"))
                        mat.SetColor("_Color", r.sharedMaterial.color);
                }
            }

            mat.SetInt("_StencilComp", stencilComp);
            mat.SetVector("_ClipPlane", clipPlane);
            mat.SetFloat("_UseClipPlane", useClipPlane ? 1f : 0f);
            mat.SetFloat("_LightMultiplier", lightMultiplier);
            mat.SetFloat("_AtmosphereIntensity", atmosphereIntensity);
            mat.SetFloat("_WindStrength", windStrength);

            if (objName.Contains("DistantSky"))
                mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry + 5;
            else if (objName.Contains("FloatingStarlightMotes"))
                mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry + 18;
            else
                mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry + 10;

            r.sharedMaterial = mat;
        }
    }

    /// <summary>
    /// 动态更新门后世界与角色的裁剪平面、Stencil、亮度、奇观氛围强度与微风强度。
    /// </summary>
    public static void UpdatePortalTargetParams(
        GameObject root,
        bool useStencil,
        Vector4 clipPlane,
        bool useClipPlane,
        float lightMultiplier,
        float atmosphereIntensity = 1.35f,
        float windStrength = 1.0f)
    {
        if (root == null) return;
        int stencilComp = useStencil ? 3 : 8;
        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
        {
            if (!(r is MeshRenderer || r is SkinnedMeshRenderer)) continue;
            var m = r.sharedMaterial;
            if (m == null) continue;
            if (m.HasProperty("_StencilComp")) m.SetInt("_StencilComp", stencilComp);
            if (m.HasProperty("_ClipPlane")) m.SetVector("_ClipPlane", clipPlane);
            if (m.HasProperty("_UseClipPlane")) m.SetFloat("_UseClipPlane", useClipPlane ? 1f : 0f);
            if (m.HasProperty("_LightMultiplier")) m.SetFloat("_LightMultiplier", lightMultiplier);
            if (m.HasProperty("_AtmosphereIntensity")) m.SetFloat("_AtmosphereIntensity", atmosphereIntensity);
            if (m.HasProperty("_WindStrength")) m.SetFloat("_WindStrength", windStrength);
        }
    }

    public static void ApplyDoorMaterials(GameObject doorRoot, PortalConfig.FrameMode mode)
    {
        ApplyDoorSpatialMaterials(doorRoot, mode, isNightRealmHalf: false, clipPlane: Vector4.zero, useClipPlane: false, useStencil: false);
    }

    public static void ApplyDoorSpatialMaterials(
        GameObject doorRoot,
        PortalConfig.FrameMode mode,
        bool isNightRealmHalf,
        Vector4 clipPlane,
        bool useClipPlane,
        bool useStencil)
    {
        if (doorRoot == null) return;

        Shader refShader = Shader.Find("Suzume/DoorFrame") ?? Shader.Find("Standard");
        Shader occShader = Shader.Find("Suzume/DoorOcclusion") ?? Shader.Find("Suzume/PortalMask");

        foreach (var mr in doorRoot.GetComponentsInChildren<MeshRenderer>(true))
        {
            if (mode == PortalConfig.FrameMode.Hidden)
            {
                mr.enabled = false;
                continue;
            }

            mr.enabled = true;
            if (mode == PortalConfig.FrameMode.Occlusion)
            {
                var occMat = new Material(occShader)
                {
                    name = "DoorOcclusion_" + mr.gameObject.name,
                    hideFlags = HideFlags.DontSave
                };
                mr.sharedMaterial = occMat;
                continue;
            }

            string objName = CleanName(mr.gameObject.name);
            string matName = mr.sharedMaterial != null ? CleanName(mr.sharedMaterial.name) : "";
            string key = objName + "|" + matName;

            var existing = mr.sharedMaterial;
            Material mat;
            if (existing != null && existing.shader == refShader && existing.name.StartsWith("DoorRef_"))
            {
                mat = existing;
            }
            else
            {
                mat = new Material(refShader)
                {
                    name = "DoorRef_" + (isNightRealmHalf ? "Night_" : "Day_") + objName,
                    hideFlags = HideFlags.DontSave
                };

                Texture2D tex = null;
                Color col = new Color(0.88f, 0.89f, 0.86f, 1f);

                if (key.Contains("283D72A6") || key.Contains("5932C1F0") || key.Contains("Reference_pigments"))
                {
                    tex = LoadTexture("model-texture-E6DD59F3-52BA-49F3-A943-D0F386B577E6");
                    col = Color.white;
                }
                else if (key.Contains("49F1B541") || key.Contains("5CED9BA5") || key.Contains("72F6F0D5") ||
                         key.Contains("0BC887AE") || key.Contains("7378BEF7") || key.Contains("D93CF93C") ||
                         key.Contains("surface_009") || key.Contains("surface_010") ||
                         key.Contains("surface_013") || key.Contains("surface_014") ||
                         key.Contains("Material_007") || key.Contains("Material_008"))
                {
                    tex = LoadTexture("model-texture-5C78C916-63B0-4634-87BB-FE87FBD47321");
                    col = Color.white;
                }
                else if (key.Contains("5FC5CEBB") || key.Contains("0742C95F") || key.Contains("surface_008") || key.Contains("surface_012"))
                {
                    col = new Color(0.16f, 0.23f, 0.18f, 1f);
                }
                else if (key.Contains("BAA9574F") || key.Contains("066F172D") || key.Contains("surface_011") || key.Contains("surface_015"))
                {
                    col = new Color(0.42f, 0.30f, 0.14f, 1f);
                }
                else if (key.Contains("A04354BC") || key.Contains("036_Portable"))
                {
                    col = new Color(0.51f, 0.37f, 0.10f, 1f);
                }

                if (tex != null) mat.SetTexture("_MainTex", tex);
                mat.SetColor("_Color", col);
                mat.color = col;
                mr.sharedMaterial = mat;
            }

            int stencilComp = (isNightRealmHalf && useStencil) ? 3 : 8;
            mat.SetInt("_StencilRef", 1);
            mat.SetInt("_StencilComp", stencilComp);
            mat.SetVector("_ClipPlane", clipPlane);
            mat.SetFloat("_UseClipPlane", useClipPlane ? 1f : 0f);
            mat.renderQueue = isNightRealmHalf
                ? (int)UnityEngine.Rendering.RenderQueue.Geometry + 15
                : (int)UnityEngine.Rendering.RenderQueue.Geometry - 30;
        }
    }

    static string CleanName(string n)
    {
        if (string.IsNullOrEmpty(n)) return "";
        int i = n.IndexOf(" (");
        if (i > 0) n = n.Substring(0, i);
        return n.Trim();
    }
}
