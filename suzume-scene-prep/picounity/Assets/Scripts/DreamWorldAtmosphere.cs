using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 铃芽之旅 · 门后常世奇观与三维茂密草海生成器（DreamWorldAtmosphere V3）：
/// 1. 精确三角面重心插值高度场（BuildHeightFieldFromTerrain）：直接光栅化 NearMeadow 的真实三角面，毫米级贴合地形起伏；
/// 2. ForegroundLushGrassBlades：门洞视野走廊 18,000 株三维柔顺摇曳草叶（根部深翠、草尖月华青碧，彻底解决草地稀疏问题）；
/// 3. ForegroundLuminousFlowers：2,000 朵高密度五瓣星辉花簇 + 翠绿花茎；
/// 4. FloatingStarlightMotes：160 颗晶莹锐利的漂浮十字星火微粒。
/// </summary>
public static class DreamWorldAtmosphere
{
    public const string RootName = "AtmosphereWonderLayer";
    public const string GrassName = "ForegroundLushGrassBlades";
    public const string FlowersName = "ForegroundLuminousFlowers";
    public const string MotesName = "FloatingStarlightMotes";

    public static GameObject Build(Transform dreamWorldRoot)
    {
        if (dreamWorldRoot == null) return null;

        var existing = dreamWorldRoot.Find(RootName);
        if (existing != null)
        {
            if (Application.isPlaying) Object.Destroy(existing.gameObject);
            else Object.DestroyImmediate(existing.gameObject);
        }

        var container = new GameObject(RootName);
        container.transform.SetParent(dreamWorldRoot, false);
        container.transform.localPosition = Vector3.zero;
        container.transform.localRotation = Quaternion.identity;
        container.transform.localScale = Vector3.one;

        BuildHeightFieldFromTerrain(dreamWorldRoot);
        BuildForegroundLushGrass(container.transform, 28000);
        BuildForegroundFlowers(container.transform, 2200);
        BuildFloatingStarMotes(container.transform, 160);

        return container;
    }

    const int GridRes = 128;
    const float GridMinX = -16f, GridMaxX = 16f;
    const float GridMinZ = -24f, GridMaxZ = 2f;
    static float[,] _heightGrid;
    static bool _hasHeightGrid;

    /// <summary>
    /// 通过对 NearMeadow (Geometry_C7FAF2CB_003) 的三角面进行精确二维包围盒重心光栅化，
    /// 获取门洞走廊每个 (x, z) 坐标处 100% 精确的地面高度，彻底消除顶点稀疏导致的悬空或陷入地下问题。
    /// </summary>
    static void BuildHeightFieldFromTerrain(Transform dreamWorldRoot)
    {
        _hasHeightGrid = false;
        if (dreamWorldRoot == null) return;

        MeshFilter targetMf = null;
        foreach (var mf in dreamWorldRoot.GetComponentsInChildren<MeshFilter>(true))
        {
            if (mf.sharedMesh != null && (mf.name.Contains("Geometry_C7FAF2CB") || mf.name.Contains("NearMeadow")))
            {
                targetMf = mf;
                break;
            }
        }
        if (targetMf == null || targetMf.sharedMesh == null) return;

        var mesh = targetMf.sharedMesh;
        var verts = mesh.vertices;
        var tris = mesh.triangles;
        if (verts == null || tris == null || verts.Length == 0 || tris.Length < 3) return;

        _heightGrid = new float[GridRes, GridRes];
        bool[,] filled = new bool[GridRes, GridRes];
        Matrix4x4 toRoot = dreamWorldRoot.worldToLocalMatrix * targetMf.transform.localToWorldMatrix;

        Vector3[] wVerts = new Vector3[verts.Length];
        for (int i = 0; i < verts.Length; i++)
        {
            wVerts[i] = toRoot.MultiplyPoint3x4(verts[i]);
        }

        float invSpanX = (GridRes - 1) / (GridMaxX - GridMinX);
        float invSpanZ = (GridRes - 1) / (GridMaxZ - GridMinZ);
        float stepX = (GridMaxX - GridMinX) / (GridRes - 1);
        float stepZ = (GridMaxZ - GridMinZ) / (GridRes - 1);

        int filledCount = 0;
        for (int t = 0; t < tris.Length; t += 3)
        {
            Vector3 a = wVerts[tris[t]];
            Vector3 b = wVerts[tris[t + 1]];
            Vector3 c = wVerts[tris[t + 2]];

            float minX = Mathf.Min(a.x, Mathf.Min(b.x, c.x));
            float maxX = Mathf.Max(a.x, Mathf.Max(b.x, c.x));
            float minZ = Mathf.Min(a.z, Mathf.Min(b.z, c.z));
            float maxZ = Mathf.Max(a.z, Mathf.Max(b.z, c.z));

            if (maxX < GridMinX || minX > GridMaxX || maxZ < GridMinZ || minZ > GridMaxZ)
                continue;

            int ixMin = Mathf.Clamp(Mathf.FloorToInt((minX - GridMinX) * invSpanX), 0, GridRes - 1);
            int ixMax = Mathf.Clamp(Mathf.CeilToInt((maxX - GridMinX) * invSpanX), 0, GridRes - 1);
            int izMin = Mathf.Clamp(Mathf.FloorToInt((minZ - GridMinZ) * invSpanZ), 0, GridRes - 1);
            int izMax = Mathf.Clamp(Mathf.CeilToInt((maxZ - GridMinZ) * invSpanZ), 0, GridRes - 1);

            float denom = (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z);
            if (Mathf.Abs(denom) < 1e-6f) continue;
            float invDenom = 1f / denom;

            for (int iz = izMin; iz <= izMax; iz++)
            {
                float pz = GridMinZ + iz * stepZ;
                for (int ix = ixMin; ix <= ixMax; ix++)
                {
                    float px = GridMinX + ix * stepX;
                    float w1 = ((b.z - c.z) * (px - c.x) + (c.x - b.x) * (pz - c.z)) * invDenom;
                    float w2 = ((c.z - a.z) * (px - c.x) + (a.x - c.x) * (pz - c.z)) * invDenom;
                    float w3 = 1f - w1 - w2;
                    if (w1 >= -0.02f && w2 >= -0.02f && w3 >= -0.02f)
                    {
                        float py = w1 * a.y + w2 * b.y + w3 * c.y;
                        if (!filled[ix, iz] || py > _heightGrid[ix, iz])
                        {
                            _heightGrid[ix, iz] = py;
                            if (!filled[ix, iz])
                            {
                                filled[ix, iz] = true;
                                filledCount++;
                            }
                        }
                    }
                }
            }
        }

        for (int iz = 0; iz < GridRes; iz++)
        {
            for (int ix = 0; ix < GridRes; ix++)
            {
                if (!filled[ix, iz]) _heightGrid[ix, iz] = -0.12f;
            }
        }
        _hasHeightGrid = filledCount > 128;
    }

    public static float SampleGroundY(float x, float z)
    {
        if (_hasHeightGrid && _heightGrid != null)
        {
            float u = Mathf.Clamp01((x - GridMinX) / (GridMaxX - GridMinX)) * (GridRes - 1);
            float v = Mathf.Clamp01((z - GridMinZ) / (GridMaxZ - GridMinZ)) * (GridRes - 1);
            int x0 = Mathf.Clamp(Mathf.FloorToInt(u), 0, GridRes - 2);
            int z0 = Mathf.Clamp(Mathf.FloorToInt(v), 0, GridRes - 2);
            float tx = u - x0;
            float tz = v - z0;
            float h0 = Mathf.Lerp(_heightGrid[x0, z0], _heightGrid[x0 + 1, z0], tx);
            float h1 = Mathf.Lerp(_heightGrid[x0, z0 + 1], _heightGrid[x0 + 1, z0 + 1], tx);
            return Mathf.Lerp(h0, h1, tz);
        }
        return -0.12f;
    }

    /// <summary>
    /// 在门后近景与中景（X ∈ [-12m, +12m], Z ∈ [-0.05m, -18m]）构建 28,000 株纤细柔顺的三维草叶，
    /// 边缘采用高斯高度衰减，与远景程序化草地 100% 无缝融合（消除 V 字形边界）。
    /// </summary>
    static void BuildForegroundLushGrass(Transform parent, int bladeCount)
    {
        var verts = new List<Vector3>(bladeCount * 5);
        var norms = new List<Vector3>(bladeCount * 5);
        var uvs = new List<Vector2>(bladeCount * 5);
        var cols = new List<Color>(bladeCount * 5);
        var tris = new List<int>(bladeCount * 9);

        Random.State oldState = Random.state;
        Random.InitState(20260818);

        for (int i = 0; i < bladeCount; i++)
        {
            float u = Random.value;
            float z = -Mathf.Lerp(0.05f, 17.5f, Mathf.Pow(u, 1.35f));

            // 60% 分布在宽广草坪 (-11.5m ~ +11.5m)，40% 加密门洞走廊，使用高斯采样消除硬边界
            float g = (Random.value + Random.value + Random.value - 1.5f) * 1.35f;
            float spreadX = (i % 5 < 3) ? (2.2f + Mathf.Abs(z) * 0.62f) : (0.95f + Mathf.Abs(z) * 0.35f);
            float x = Mathf.Clamp(g * spreadX, -13.5f, 13.5f);

            // 边缘高度平滑过渡系数，使三维草丛自然汇入地面肌理
            float edgeRatio = Mathf.Abs(x) / Mathf.Max(2.5f, 2.2f + Mathf.Abs(z) * 0.65f);
            float distRatio = Mathf.Abs(z) / 17.5f;
            float heightScale = Mathf.Clamp(1.05f - 0.38f * edgeRatio - 0.30f * distRatio, 0.42f, 1.0f);

            float gY = SampleGroundY(x, z) - 0.008f;
            float bladeH = Random.Range(0.065f, 0.155f) * heightScale;
            float halfW = Random.Range(0.0045f, 0.0095f);

            float yaw = Random.Range(0f, Mathf.PI * 2f);
            float bend = Random.Range(0.018f, 0.055f) * heightScale;
            Vector3 right = new Vector3(Mathf.Cos(yaw), 0f, -Mathf.Sin(yaw));
            Vector3 forward = new Vector3(Mathf.Sin(yaw), 0f, Mathf.Cos(yaw));

            Vector3 pRootL = new Vector3(x, gY, z) - right * halfW;
            Vector3 pRootR = new Vector3(x, gY, z) + right * halfW;
            Vector3 pMidL  = new Vector3(x, gY + bladeH * 0.52f, z) - right * (halfW * 0.60f) + forward * (bend * 0.45f);
            Vector3 pMidR  = new Vector3(x, gY + bladeH * 0.52f, z) + right * (halfW * 0.60f) + forward * (bend * 0.45f);
            Vector3 pTip   = new Vector3(x, gY + bladeH, z) + forward * bend;

            Vector3 nrm = Vector3.Normalize(Vector3.up + forward * 0.25f);
            Color tipTone = Color.Lerp(
                new Color(0.105f, 0.295f, 0.175f, 1f),
                new Color(0.165f, 0.395f, 0.255f, 1f),
                Random.value
            );

            int b = verts.Count;
            verts.Add(pRootL); verts.Add(pRootR);
            verts.Add(pMidL);  verts.Add(pMidR);
            verts.Add(pTip);

            for (int k = 0; k < 5; k++)
            {
                norms.Add(nrm);
                cols.Add(tipTone);
            }
            uvs.Add(new Vector2(0f, 0f));
            uvs.Add(new Vector2(1f, 0f));
            uvs.Add(new Vector2(0f, 0.52f));
            uvs.Add(new Vector2(1f, 0.52f));
            uvs.Add(new Vector2(0.5f, 1f));

            tris.Add(b + 0); tris.Add(b + 2); tris.Add(b + 1);
            tris.Add(b + 1); tris.Add(b + 2); tris.Add(b + 3);
            tris.Add(b + 2); tris.Add(b + 4); tris.Add(b + 3);
        }

        Random.state = oldState;

        var grassGo = new GameObject(GrassName);
        grassGo.transform.SetParent(parent, false);
        var mf = grassGo.AddComponent<MeshFilter>();
        var mr = grassGo.AddComponent<MeshRenderer>();
        var mesh = new Mesh { name = GrassName + "_Mesh", hideFlags = HideFlags.DontSave };
        mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
        mesh.SetVertices(verts);
        mesh.SetNormals(norms);
        mesh.SetUVs(0, uvs);
        mesh.SetColors(cols);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateBounds();
        mf.sharedMesh = mesh;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
    }

    /// <summary>
    /// 为门外现实庭院（X ∈ [-9m, +9m], Z ∈ [-10m, +4.2m]，由 Stencil NotEqual 1 自动避开门洞内部）
    /// 生成 12,000 株自然纤细的三维青草草丛，彻底替代方格网地面。
    /// </summary>
    public static GameObject BuildCourtyardGrassPatch(Transform parent, int bladeCount = 12000)
    {
        var verts = new List<Vector3>(bladeCount * 5);
        var norms = new List<Vector3>(bladeCount * 5);
        var uvs = new List<Vector2>(bladeCount * 5);
        var cols = new List<Color>(bladeCount * 5);
        var tris = new List<int>(bladeCount * 9);

        Random.State oldState = Random.state;
        Random.InitState(20260909);

        for (int i = 0; i < bladeCount; i++)
        {
            float t = Random.value;
            float z = Mathf.Lerp(3.8f, -10.5f, Mathf.Pow(t, 1.35f));
            float distFromCam = Mathf.Max(0.4f, 3.2f - z);
            float halfSpanX = 1.6f + distFromCam * 0.68f;
            float x = Random.Range(-halfSpanX, halfSpanX);

            // 避开门框正中间的窄矩形开口区 (|x| < 0.44m, z < 0.05m)，其余门外区域全覆盖
            if (Mathf.Abs(x) < 0.45f && z < 0.05f && z > -1.5f)
            {
                x = (x >= 0f ? 0.48f : -0.48f) + Random.Range(-0.25f, 0.25f);
            }

            float heightScale = Mathf.Clamp(1.0f - (distFromCam / 16.0f) * 0.45f, 0.45f, 1.0f);
            float gY = -0.025f;
            float bladeH = Random.Range(0.055f, 0.130f) * heightScale;
            float halfW = Random.Range(0.0045f, 0.0090f);

            float yaw = Random.Range(0f, Mathf.PI * 2f);
            float bend = Random.Range(0.015f, 0.045f) * heightScale;
            Vector3 right = new Vector3(Mathf.Cos(yaw), 0f, -Mathf.Sin(yaw));
            Vector3 forward = new Vector3(Mathf.Sin(yaw), 0f, Mathf.Cos(yaw));

            Vector3 pRootL = new Vector3(x, gY, z) - right * halfW;
            Vector3 pRootR = new Vector3(x, gY, z) + right * halfW;
            Vector3 pMidL  = new Vector3(x, gY + bladeH * 0.52f, z) - right * (halfW * 0.60f) + forward * (bend * 0.45f);
            Vector3 pMidR  = new Vector3(x, gY + bladeH * 0.52f, z) + right * (halfW * 0.60f) + forward * (bend * 0.45f);
            Vector3 pTip   = new Vector3(x, gY + bladeH, z) + forward * bend;

            Vector3 nrm = Vector3.Normalize(Vector3.up + forward * 0.25f);
            Color tipTone = Color.Lerp(
                new Color(0.105f, 0.285f, 0.165f, 1f),
                new Color(0.160f, 0.375f, 0.235f, 1f),
                Random.value
            );

            int b = verts.Count;
            verts.Add(pRootL); verts.Add(pRootR);
            verts.Add(pMidL);  verts.Add(pMidR);
            verts.Add(pTip);

            for (int k = 0; k < 5; k++)
            {
                norms.Add(nrm);
                cols.Add(tipTone);
            }
            uvs.Add(new Vector2(0f, 0f));
            uvs.Add(new Vector2(1f, 0f));
            uvs.Add(new Vector2(0f, 0.52f));
            uvs.Add(new Vector2(1f, 0.52f));
            uvs.Add(new Vector2(0.5f, 1f));

            tris.Add(b + 0); tris.Add(b + 2); tris.Add(b + 1);
            tris.Add(b + 1); tris.Add(b + 2); tris.Add(b + 3);
            tris.Add(b + 2); tris.Add(b + 4); tris.Add(b + 3);
        }

        Random.state = oldState;

        var grassGo = new GameObject("CourtyardLushGrassBlades");
        grassGo.transform.SetParent(parent, false);
        var mf = grassGo.AddComponent<MeshFilter>();
        var mr = grassGo.AddComponent<MeshRenderer>();
        var mesh = new Mesh { name = "CourtyardLushGrass_Mesh", hideFlags = HideFlags.DontSave };
        mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
        mesh.SetVertices(verts);
        mesh.SetNormals(norms);
        mesh.SetUVs(0, uvs);
        mesh.SetColors(cols);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateBounds();
        mf.sharedMesh = mesh;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        return grassGo;
    }

    static void BuildForegroundFlowers(Transform parent, int flowerCount)
    {
        var fVerts = new List<Vector3>(flowerCount * 11);
        var fNorms = new List<Vector3>(flowerCount * 11);
        var fUVs = new List<Vector2>(flowerCount * 11);
        var fCols = new List<Color>(flowerCount * 11);
        var fTris = new List<int>(flowerCount * 5 * 3);

        Color[] palette = new Color[]
        {
            new Color(0.16f, 0.48f, 0.98f, 1f), // 宝石矢车菊蓝 (46%)
            new Color(0.58f, 0.22f, 0.94f, 1f), // 星云紫罗兰 (30%)
            new Color(0.92f, 0.32f, 0.68f, 1f), // 暮光樱花粉 (14%)
            new Color(0.98f, 0.64f, 0.16f, 1f)  // 暖琥珀金 (10%)
        };

        Random.State oldState = Random.state;
        Random.InitState(20260528);

        Vector2[] clusterCenters = new Vector2[95];
        int[] clusterTone = new int[95];
        for (int c = 0; c < clusterCenters.Length; c++)
        {
            float t = (float)c / clusterCenters.Length;
            float cz = -Mathf.Lerp(0.45f, 14.5f, Mathf.Pow(t, 1.15f));
            float maxSpreadX = 0.60f + Mathf.Abs(cz) * 0.44f;
            float cx = Random.Range(-maxSpreadX, maxSpreadX);
            clusterCenters[c] = new Vector2(cx, cz);

            float r = Random.value;
            clusterTone[c] = r < 0.46f ? 0 : (r < 0.76f ? 1 : (r < 0.90f ? 2 : 3));
        }

        for (int i = 0; i < flowerCount; i++)
        {
            int cIdx = i % clusterCenters.Length;
            Vector2 center = clusterCenters[cIdx];
            float ang = Random.Range(0f, Mathf.PI * 2f);
            float rad = Mathf.Sqrt(Random.value) * Random.Range(0.28f, 1.05f);
            float x = center.x + Mathf.Cos(ang) * rad;
            float z = Mathf.Min(-0.22f, center.y + Mathf.Sin(ang) * rad);

            Vector2 toChar = new Vector2(x, z - (-2.7f));
            if (toChar.magnitude < 0.25f)
            {
                x += (x >= 0f ? 0.28f : -0.28f);
            }

            float gY = SampleGroundY(x, z);
            float stemH = Random.Range(0.08f, 0.17f);
            float flowerR = Random.Range(0.022f, 0.040f);

            Quaternion tilt = Quaternion.Euler(Random.Range(-20f, 20f), Random.Range(0f, 360f), Random.Range(-20f, 20f));
            Vector3 headPos = new Vector3(x, gY + stemH, z);
            Vector3 upDir = (tilt * Vector3.up).normalized;

            int tone = (Random.value < 0.84f) ? clusterTone[cIdx] : Random.Range(0, palette.Length);
            float shade = Random.Range(0.78f, 1.12f);
            Color petalCol = new Color(
                Mathf.Clamp01(palette[tone].r * shade),
                Mathf.Clamp01(palette[tone].g * shade),
                Mathf.Clamp01(palette[tone].b * shade),
                1f
            );
            Color coreCol = Color.Lerp(petalCol, new Color(1.0f, 0.85f, 0.38f, 1f), 0.58f);

            int fb = fVerts.Count;
            fVerts.Add(headPos);
            fNorms.Add(upDir);
            fUVs.Add(new Vector2(0.5f, 0.0f));
            fCols.Add(coreCol);

            for (int p = 0; p < 5; p++)
            {
                float a0 = (p * 72f - 24f) * Mathf.Deg2Rad;
                float a1 = (p * 72f + 24f) * Mathf.Deg2Rad;
                Vector3 local0 = new Vector3(Mathf.Cos(a0) * flowerR, flowerR * 0.22f, Mathf.Sin(a0) * flowerR);
                Vector3 local1 = new Vector3(Mathf.Cos(a1) * flowerR, flowerR * 0.22f, Mathf.Sin(a1) * flowerR);
                Vector3 p0 = headPos + tilt * local0;
                Vector3 p1 = headPos + tilt * local1;

                fVerts.Add(p0);
                fVerts.Add(p1);
                fNorms.Add(upDir);
                fNorms.Add(upDir);
                fUVs.Add(new Vector2(0f, 1f));
                fUVs.Add(new Vector2(1f, 1f));
                fCols.Add(petalCol);
                fCols.Add(petalCol);

                int v0 = fb + 1 + p * 2;
                int v1 = v0 + 1;
                fTris.Add(fb);
                fTris.Add(v0);
                fTris.Add(v1);
            }
        }

        Random.state = oldState;

        var flowersGo = new GameObject(FlowersName);
        flowersGo.transform.SetParent(parent, false);
        var fMf = flowersGo.AddComponent<MeshFilter>();
        var fMr = flowersGo.AddComponent<MeshRenderer>();
        var fMesh = new Mesh { name = FlowersName + "_Mesh", hideFlags = HideFlags.DontSave };
        fMesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
        fMesh.SetVertices(fVerts);
        fMesh.SetNormals(fNorms);
        fMesh.SetUVs(0, fUVs);
        fMesh.SetColors(fCols);
        fMesh.SetTriangles(fTris, 0);
        fMesh.RecalculateBounds();
        fMf.sharedMesh = fMesh;
        fMr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
    }

    static void BuildFloatingStarMotes(Transform parent, int moteCount)
    {
        var verts = new List<Vector3>(moteCount * 4);
        var norms = new List<Vector3>(moteCount * 4);
        var uvs = new List<Vector2>(moteCount * 4);
        var cols = new List<Color>(moteCount * 4);
        var tris = new List<int>(moteCount * 6);

        Color[] motePalette = new Color[]
        {
            new Color(0.45f, 0.84f, 1.00f, 0.90f),
            new Color(1.00f, 0.82f, 0.40f, 0.92f),
            new Color(0.92f, 0.58f, 1.00f, 0.88f)
        };

        Random.State oldState = Random.state;
        Random.InitState(20261017);

        for (int i = 0; i < moteCount; i++)
        {
            float t = Random.value;
            float z = -Mathf.Lerp(0.65f, 16.0f, Mathf.Pow(t, 1.15f));
            float spreadX = 0.50f + Mathf.Abs(z) * 0.38f;
            float x = Random.Range(-spreadX, spreadX);
            float y = Random.Range(0.22f, 2.20f + Mathf.Abs(z) * 0.06f);

            // 精致小巧的星火微粒，避免近处过大模糊
            float size = Random.Range(0.007f, 0.015f) * (1f + Mathf.Abs(z) * 0.025f);
            float sharedSeed = Random.value;
            Color c = motePalette[i % motePalette.Length];

            Vector3 center = new Vector3(x, y, z);
            Vector3 right = new Vector3(size, 0f, 0f);
            Vector3 up = new Vector3(0f, size, 0f);

            int b = verts.Count;
            verts.Add(center - right - up);
            verts.Add(center - right + up);
            verts.Add(center + right + up);
            verts.Add(center + right - up);

            for (int k = 0; k < 4; k++)
            {
                norms.Add(new Vector3(0f, 0f, sharedSeed));
                cols.Add(c);
            }
            uvs.Add(new Vector2(0f, 0f));
            uvs.Add(new Vector2(0f, 1f));
            uvs.Add(new Vector2(1f, 1f));
            uvs.Add(new Vector2(1f, 0f));

            tris.Add(b + 0); tris.Add(b + 1); tris.Add(b + 2);
            tris.Add(b + 0); tris.Add(b + 2); tris.Add(b + 3);
        }

        Random.state = oldState;

        var motesGo = new GameObject(MotesName);
        motesGo.transform.SetParent(parent, false);
        var mf = motesGo.AddComponent<MeshFilter>();
        var mr = motesGo.AddComponent<MeshRenderer>();
        var mesh = new Mesh { name = MotesName + "_Mesh", hideFlags = HideFlags.DontSave };
        mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
        mesh.SetVertices(verts);
        mesh.SetNormals(norms);
        mesh.SetUVs(0, uvs);
        mesh.SetColors(cols);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateBounds();
        mf.sharedMesh = mesh;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        mr.receiveShadows = false;
    }
}
