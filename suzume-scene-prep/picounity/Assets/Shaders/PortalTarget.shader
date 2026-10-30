// 门后梦幻世界（常世）、3D 茂密草海与角色专用 Shader（超清锐利版 V3 — 毫米级草叶肌理 + 针尖星芒 + 6阶高清云海）：
// 1. Stencil 门洞裁剪（默认 Comp Equal, Ref 1；全花海预览或庭院外草坪可切换）
// 2. 门洞平面裁剪（_ClipPlane），精确分离门内常世（Z<=0）与门外庭院（Z>=0）。
// 3. 天幕奇观模式（_IsSkyDome=1）：
//    - 采用 6 阶高频程序化暮云与银河星云，彻底消除球面贴图在门框小视场角下的 90 像素拉伸模糊；
//    - 针尖级高密星空（240x300 / 110x140 / 52x68）+ 纤细锐利十字衍射星芒。
// 4. 地面与三维草海模式（_IsTerrain=1 / _IsGrass=1）：
//    - 解决原烘焙地面贴图 247m 跨度导致的 12cm/像素模糊问题，内置 45x/135x 双尺度毫米级程序化草丝与伪法线光影；
//    - 配合 24,000+ 株三维锥形草叶（根部深翠、草尖青碧透光）随微风起伏。
Shader "Suzume/PortalTarget"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo (RGB)", 2D) = "white" {}
        [Normal] _BumpMap ("Normal Map", 2D) = "bump" {}
        _UseNormalMap ("Use Normal Map", Float) = 0
        _Roughness ("Roughness", Range(0,1)) = 0.8
        [HDR] _EmissionColor ("Emission Color", Color) = (0,0,0,1)
        _EmissionStrength ("Emission Strength", Float) = 0
        _UseMainTexAsEmission ("Use MainTex As Emission", Float) = 0
        _Unlit ("Unlit Mode (1=Sky/Stars, 0=Lit)", Float) = 0
        _IsSkyDome ("Is Sky Dome", Float) = 0
        _IsFlower ("Is Flower Mesh", Float) = 0
        _IsGrass ("Is Grass Mesh", Float) = 0
        _IsTerrain ("Is Terrain Mesh", Float) = 0
        _IsStarMote ("Is Floating Star Mote", Float) = 0
        _WindStrength ("Wind Sway Strength", Float) = 1.0
        _AtmosphereIntensity ("Atmosphere Wonder Intensity", Float) = 1.38
        _LightMultiplier ("Light Multiplier", Float) = 1.18
        _Alpha ("Alpha", Range(0,1)) = 1.0
        _ClipPlane ("Portal Clip Plane (World nx,ny,nz,d)", Vector) = (0, 0, -1, 0)
        _UseClipPlane ("Use Portal Clip Plane", Float) = 1.0
        [Enum(UnityEngine.Rendering.CompareFunction)] _StencilComp ("Stencil Comp", Float) = 3
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry+10" "IgnoreProjector"="True" }

        Cull Off
        ZWrite On
        Blend SrcAlpha OneMinusSrcAlpha

        Stencil
        {
            Ref 1
            Comp [_StencilComp]
        }

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float4 tangent : TANGENT;
                float2 uv : TEXCOORD0;
                fixed4 color : COLOR;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 worldPos : TEXCOORD1;
                float3 worldNormal : TEXCOORD2;
                fixed4 vertColor : COLOR;
            };

            fixed4 _Color;
            sampler2D _MainTex;
            float4 _MainTex_ST;
            sampler2D _BumpMap;
            float _UseNormalMap;
            float _Roughness;
            float4 _EmissionColor;
            float _EmissionStrength;
            float _UseMainTexAsEmission;
            float _Unlit;
            float _IsSkyDome;
            float _IsFlower;
            float _IsGrass;
            float _IsTerrain;
            float _IsStarMote;
            float _WindStrength;
            float _AtmosphereIntensity;
            float _LightMultiplier;
            float _Alpha;
            float4 _ClipPlane;
            float _UseClipPlane;

            float hash21(float2 p)
            {
                p = frac(p * float2(234.34, 435.345));
                p += dot(p, p + 34.23);
                return frac(p.x * p.y);
            }

            float2 hash22(float2 p)
            {
                float n = hash21(p);
                return float2(n, hash21(p + n + 17.3));
            }

            float noise2D(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                float a = hash21(i);
                float b = hash21(i + float2(1.0, 0.0));
                float c = hash21(i + float2(0.0, 1.0));
                float d = hash21(i + float2(1.0, 1.0));
                return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
            }

            float fbm4(float2 p)
            {
                float v = 0.0;
                float a = 0.5;
                float2 shift = float2(100.0, 100.0);
                for (int idx = 0; idx < 4; idx++)
                {
                    v += a * noise2D(p);
                    p = p * 2.03 + shift;
                    a *= 0.5;
                }
                return v;
            }

            float fbm6(float2 p)
            {
                float v = 0.0;
                float a = 0.5;
                float2x2 rot = float2x2(0.80, -0.60, 0.60, 0.80);
                for (int idx = 0; idx < 6; idx++)
                {
                    v += a * noise2D(p);
                    p = mul(rot, p) * 2.04 + float2(37.2, 71.8);
                    a *= 0.5;
                }
                return v;
            }

            // 电影级软色调映射：保留高光饱和色彩，防止 RGB 过曝发白
            float3 SoftToneMap(float3 c)
            {
                return c / (1.0 + c * 0.42);
            }

            // 针尖级锐利星空采样（晶莹锐核 + 微光晕 + 纤细十字衍射星芒 + 呼吸闪烁）
            float3 evalStarLayer(float2 uvGrid, float densityThreshold, float flareStrength, float timeSec)
            {
                float2 cell = floor(uvGrid);
                float2 f = frac(uvGrid) - 0.5;
                float rnd = hash21(cell);
                if (rnd < densityThreshold) return float3(0, 0, 0);

                float2 offset = float2(hash21(cell + 13.7), hash21(cell + 71.3)) - 0.5;
                float2 p = (f - offset * 0.56) * 2.0;
                float r2 = dot(p, p);

                float twinkle = 0.80 + 0.20 * sin(timeSec * (2.0 + frac(rnd * 17.0) * 3.8) + rnd * 62.8);
                // 高锐度星核：半径收缩 5 倍，拒绝模糊棉球感
                float core = exp(-r2 * 240.0);
                float halo = exp(-r2 * 38.0) * 0.26;
                float crossRay = 0.0;
                if (flareStrength > 0.01)
                {
                    crossRay = (exp(-abs(p.x) * 135.0) * exp(-abs(p.y) * 5.2) +
                                exp(-abs(p.y) * 135.0) * exp(-abs(p.x) * 5.2)) * flareStrength;
                }

                float3 starTint = lerp(
                    float3(0.68, 0.88, 1.00),
                    lerp(float3(1.00, 0.88, 0.68), float3(0.95, 0.72, 1.00), frac(rnd * 31.7)),
                    frac(rnd * 11.3)
                );
                float3 rgb = lerp(starTint, float3(1.0, 1.0, 1.0), saturate(core * 1.4));
                return rgb * ((core * 1.85 + halo + crossRay) * twinkle);
            }

            v2f vert (appdata v)
            {
                v2f o;
                float3 wPos = mul(unity_ObjectToWorld, v.vertex).xyz;

                float t = _Time.y;
                if (_IsGrass > 0.5 && _WindStrength > 0.001)
                {
                    // 三维草叶：按 uv.y (0=草根固定, 1=草尖摇摆) 或局部高度产生柔顺风浪摇曳
                    float tipFactor = (v.uv.y > 0.01) ? (v.uv.y * v.uv.y) : saturate((v.vertex.y + 0.15) * 2.8);
                    float gust = sin(t * 2.3 + wPos.x * 1.5 + wPos.z * 1.2) * 0.032
                               + cos(t * 3.8 + wPos.x * 3.1 - wPos.z * 2.4) * 0.014;
                    wPos.x += gust * tipFactor * _WindStrength;
                    wPos.z += gust * 0.65 * tipFactor * _WindStrength;
                }
                else if (_IsFlower > 0.5 && _WindStrength > 0.001)
                {
                    float heightFactor = saturate((v.vertex.y + 0.15) * 2.5);
                    float wave = sin(t * 2.1 + wPos.x * 1.7 + wPos.z * 1.3) * 0.020
                               + cos(t * 3.4 + wPos.x * 2.9 - wPos.z * 2.1) * 0.009;
                    wPos.x += wave * heightFactor * _WindStrength;
                    wPos.z += wave * 0.6 * heightFactor * _WindStrength;
                }
                else if (_IsStarMote > 0.5)
                {
                    float seed = v.normal.z * 50.0;
                    wPos.y += sin(t * 1.3 + seed) * 0.055;
                    wPos.x += cos(t * 0.9 + seed * 1.4) * 0.035;
                }

                o.pos = mul(UNITY_MATRIX_VP, float4(wPos, 1.0));
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldPos = wPos;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                o.vertColor = v.color;
                return o;
            }

            float3 ComputeTwilightSky(float3 viewDir, float3 bakedTexRGB, float timeSec, float wonder)
            {
                float3 v = normalize(viewDir);
                float y = max(v.y, 0.0);
                float eastMix = smoothstep(-0.55, 0.50, v.x);

                // 1) 常世三段暮色天幕（左暖珊瑚红金 ↔ 右冷松石青碧 -> 中空星云紫罗兰/深海蓝 -> 天顶深靛蓝）
                float3 horizonWarm = float3(0.82, 0.35, 0.36);
                float3 horizonCool = float3(0.16, 0.50, 0.68);
                float3 horizonCol = lerp(horizonWarm, horizonCool, eastMix);

                float3 midWarm = float3(0.32, 0.11, 0.40);
                float3 midCool = float3(0.09, 0.22, 0.50);
                float3 midCol = lerp(midWarm, midCool, eastMix);

                float3 upperCol = lerp(float3(0.08, 0.05, 0.22), float3(0.04, 0.10, 0.28), eastMix);
                float3 zenithCol = float3(0.02, 0.03, 0.09);

                float3 procSky = lerp(horizonCol, midCol, smoothstep(0.00, 0.075, y));
                procSky = lerp(procSky, upperCol, smoothstep(0.07, 0.22, y));
                procSky = lerp(procSky, zenithCol, smoothstep(0.20, 0.65, y));

                float horizonBand = exp(-pow((y - 0.018) / 0.030, 2.0));
                procSky += lerp(float3(0.88, 0.44, 0.28), float3(0.24, 0.60, 0.80), eastMix * 0.6)
                           * (horizonBand * 0.25 * wonder);

                // 2) 斜穿门洞视野的高清银河星云带（6 阶 FBM 细腻星云丝缕与暗尘裂隙）
                float2 skyProj = float2(atan2(v.x, -v.z), y);
                float galacticAxis = (skyProj.y - 0.105) - skyProj.x * 0.26;
                float galacticProfile = exp(-pow(galacticAxis / 0.066, 2.0)) * smoothstep(0.01, 0.045, y);
                float nebulaNoise1 = fbm6(skyProj * float2(11.0, 24.0) + float2(timeSec * 0.006, 0.0));
                float nebulaNoise2 = fbm6(skyProj * float2(24.0, 52.0) - float2(0.0, timeSec * 0.009));

                float3 nebulaCore = lerp(float3(0.22, 0.54, 0.98), float3(0.78, 0.26, 0.74), nebulaNoise1);
                float3 nebulaGold = float3(0.96, 0.64, 0.36) * smoothstep(0.48, 0.78, nebulaNoise2);
                float dustRift = smoothstep(0.34, 0.68, fbm6(skyProj * float2(28.0, 56.0) + 5.2));
                float3 milkyWay = (nebulaCore * (0.38 + 0.58 * nebulaNoise1) + nebulaGold * 0.36)
                                  * galacticProfile * (0.32 + 0.68 * dustRift) * wonder;
                procSky += milkyWay;

                // 3) 6 阶程序化高清暮云（替代原本仅 90 像素宽的低清贴图云，边缘锐利、带金红霞光透射）
                float cloudZone = smoothstep(0.002, 0.025, y) * (1.0 - smoothstep(0.09, 0.22, y));
                if (cloudZone > 0.001)
                {
                    float2 cloudUV = float2(skyProj.x * 9.5 + timeSec * 0.012, y * 42.0);
                    float cBase = fbm6(cloudUV);
                    float cDetail = fbm4(cloudUV * 3.2 - float2(timeSec * 0.02, 1.7));
                    float cDensity = smoothstep(0.46, 0.76, cBase * 0.75 + cDetail * 0.25) * cloudZone;
                    float cEdge = smoothstep(0.42, 0.54, cBase * 0.75 + cDetail * 0.25) - smoothstep(0.54, 0.72, cBase * 0.75 + cDetail * 0.25);

                    float3 cloudBody = lerp(float3(0.14, 0.11, 0.24), float3(0.28, 0.18, 0.34), eastMix * 0.5)
                                     + bakedTexRGB * 0.12;
                    float3 cloudRimCol = lerp(float3(0.96, 0.52, 0.38), float3(0.45, 0.72, 0.92), eastMix * 0.45);
                    float3 crispCloud = cloudBody + cloudRimCol * (max(0.0, cEdge) * 1.15 * wonder);
                    procSky = lerp(procSky, crispCloud, saturate(cDensity * 0.68));
                }

                procSky = SoftToneMap(procSky);

                // 4) 三层针尖级高密闪烁繁星与十字星芒（高网格密度，彻底告别糊成一团的棉球星）
                float starFade = smoothstep(0.012, 0.042, y);
                if (starFade > 0.001)
                {
                    float3 starsFine = evalStarLayer(skyProj * float2(240.0, 300.0), 0.86 - 0.08 * galacticProfile, 0.0, timeSec) * 0.85;
                    float3 starsMid  = evalStarLayer(skyProj * float2(112.0, 145.0) + 19.3, 0.93 - 0.04 * galacticProfile, 0.42, timeSec) * 1.35;
                    float3 starsHero = evalStarLayer(skyProj * float2(52.0, 68.0) + 47.1, 0.965, 0.95, timeSec) * 2.10;
                    procSky += (starsFine + starsMid + starsHero) * starFade * wonder;
                }

                return procSky;
            }

            // 毫米级程序化草地肌理（近处根根分明，远处自动平滑抗噪，彻底解决 247m 大地形贴图模糊与远景噪点）
            void EvaluateCrispMeadowSurface(
                float3 worldPos,
                float timeSec,
                float wonder,
                inout float3 baseRGB,
                inout float3 worldNormal,
                inout float3 emission)
            {
                float2 xz = worldPos.xz;
                float camDist = length(_WorldSpaceCameraPos - worldPos);
                // 近景 (0~8m) 保留 100% 毫米级草丝锐度，中远景 (8~28m) 平滑过渡为丝绒草浪，彻底消除远景摩尔纹噪点
                float microFade = 1.0 - smoothstep(6.0, 26.0, camDist);
                float midFade   = 1.0 - smoothstep(14.0, 55.0, camDist);

                float2 windDir = normalize(float2(0.82, 0.57));
                float windWave = fbm4(xz * 0.20 + windDir * (timeSec * 0.40));
                float shimmer = smoothstep(0.46, 0.78, windWave);

                // 第 1 层：草丛簇级柔波（中远景依然自然起伏）
                float clumpNoise = fbm4(xz * 3.8 + windWave * 0.25);

                // 第 2 层：厘米级草丝纤维
                float2 bladeUV1 = float2(dot(xz, float2(0.85, -0.52)) * 36.0, dot(xz, float2(0.52, 0.85)) * 14.0) + windWave * 1.1;
                float blade1 = lerp(0.5, noise2D(bladeUV1), midFade);

                // 第 3 层：毫米级近景草叶尖端
                float2 bladeUV2 = float2(dot(xz, float2(-0.60, 0.80)) * 95.0, dot(xz, float2(0.80, 0.60)) * 38.0) - windWave * 1.6;
                float blade2 = lerp(0.5, noise2D(bladeUV2), microFade);

                float bladeComposite = saturate(clumpNoise * 0.34 + blade1 * 0.40 + blade2 * 0.26);
                float bladeRidge = smoothstep(0.30, 0.76, bladeComposite);

                // 近景微法线凹凸（随距离平滑衰减，远景绝不闪烁）
                float dBladeX = ((blade1 - 0.5) * 0.22 + (blade2 - 0.5) * 0.16) * microFade;
                float dBladeZ = ((clumpNoise - 0.5) * 0.18 + (blade2 - 0.5) * 0.14) * microFade;
                worldNormal = normalize(worldNormal + float3(dBladeX, 0.0, dBladeZ));

                // 自然统一的常世深翠绿 -> 鲜草绿 -> 月华青碧草尖（与 3D 草叶颜色 100% 融为一体）
                float3 rootGreen = float3(0.042, 0.135, 0.082);
                float3 midGreen  = float3(0.092, 0.255, 0.152);
                float3 tipJade   = float3(0.155, 0.375, 0.245);
                float3 windSheen = float3(0.195, 0.460, 0.365);

                float3 procGrass = lerp(rootGreen, midGreen, smoothstep(0.22, 0.60, bladeRidge));
                procGrass = lerp(procGrass, tipJade, smoothstep(0.58, 0.88, bladeRidge));
                procGrass = lerp(procGrass, windSheen, shimmer * 0.28 * wonder * (0.4 + 0.6 * bladeRidge));

                baseRGB = lerp(baseRGB * float3(0.85, 1.22, 0.98), procGrass, 0.82);
                emission += float3(0.03, 0.10, 0.11) * ((0.30 + shimmer * 0.70) * 0.20 * wonder);
            }

            fixed4 frag (v2f i, fixed facing : VFACE) : SV_Target
            {
                if (_UseClipPlane > 0.5)
                {
                    float planeDist = dot(i.worldPos, _ClipPlane.xyz) + _ClipPlane.w;
                    clip(planeDist);
                }

                float timeSec = _Time.y;
                float wonder = max(0.2, _AtmosphereIntensity);

                // 1. 悬浮晶莹星火微粒模式（_IsStarMote = 1）
                if (_IsStarMote > 0.5)
                {
                    float2 p = (i.uv - 0.5) * 2.0;
                    float r2 = dot(p, p);
                    if (r2 > 1.0) discard;
                    float core = exp(-r2 * 36.0);
                    float halo = exp(-r2 * 7.5) * 0.38;
                    float cross = (exp(-abs(p.x) * 42.0) * exp(-abs(p.y) * 3.8) +
                                   exp(-abs(p.y) * 42.0) * exp(-abs(p.x) * 3.8)) * 0.45;
                    float pulse = 0.75 + 0.25 * sin(timeSec * 2.6 + i.worldNormal.z * 62.8);
                    float a = saturate((core + halo + cross) * pulse * i.vertColor.a);
                    if (a < 0.04) discard;
                    float3 moteRGB = lerp(i.vertColor.rgb, float3(1.0, 1.0, 1.0), saturate(core * 0.85)) * (1.35 * _LightMultiplier);
                    return fixed4(moteRGB, a);
                }

                fixed4 tex = tex2D(_MainTex, i.uv);
                bool hasVertCol = (i.vertColor.r + i.vertColor.g + i.vertColor.b) > 0.01;
                float3 baseRGB = tex.rgb * _Color.rgb * (hasVertCol ? i.vertColor.rgb : float3(1,1,1));
                float alpha = tex.a * _Color.a * _Alpha;

                // 2. 常世天幕穹顶模式（_IsSkyDome = 1）
                if (_IsSkyDome > 0.5)
                {
                    float3 skyDir = normalize(i.worldPos - float3(0, 1.2, 0));
                    float3 skyCol = ComputeTwilightSky(skyDir, tex.rgb, timeSec, wonder) * max(0.25, _LightMultiplier);
                    return fixed4(skyCol, 1.0);
                }

                float3 emissionSource = (_UseMainTexAsEmission > 0.5) ? baseRGB : _EmissionColor.rgb;
                float3 emission = emissionSource * _EmissionStrength;

                if (_Unlit > 0.5)
                {
                    float3 unlitCol = (baseRGB + emission) * max(0.25, _LightMultiplier);
                    return fixed4(unlitCol, alpha);
                }

                // 3. 暮光花海、三维草叶、草原地面与铃芽角色光照
                float3 N = normalize(i.worldNormal) * (facing >= 0 ? 1.0 : -1.0);

                // 花朵专项色彩：带放射状花瓣脉络与柔和花蕊层次
                if (_IsFlower > 0.5)
                {
                    float spatialPhase = frac(sin(dot(floor(i.worldPos.xz * 2.5), float2(12.9898, 78.233))) * 43758.5453);
                    float3 glowTint = lerp(
                        float3(0.20, 0.56, 1.00),
                        lerp(float3(0.74, 0.26, 0.96), float3(1.00, 0.68, 0.20), step(0.80, spatialPhase)),
                        step(0.48, spatialPhase)
                    );
                    if (!hasVertCol)
                    {
                        baseRGB = lerp(baseRGB * 1.15, glowTint, 0.58);
                    }
                    float petalGrad = saturate(i.uv.y);
                    float hemiF = N.y * 0.5 + 0.5;
                    float3 flowerCol = baseRGB * (0.62 + 0.45 * hemiF + 0.18 * petalGrad) + baseRGB * (0.32 * wonder);
                    flowerCol = SoftToneMap(flowerCol) * _LightMultiplier;
                    return fixed4(flowerCol, alpha);
                }
                else if (_IsTerrain > 0.5)
                {
                    EvaluateCrispMeadowSurface(i.worldPos, timeSec, wonder, baseRGB, N, emission);
                }
                else if (_IsGrass > 0.5)
                {
                    // 三维立体草叶：将法线向竖直方向柔和偏置，使草叶受光均匀翠绿，绝不产生枯红暗面
                    N = normalize(lerp(N, float3(0.0, 1.0, 0.0), 0.65));
                    float tipH = saturate(i.uv.y);
                    float windWave = fbm4(i.worldPos.xz * 0.20 + float2(timeSec * 0.40, timeSec * 0.26));
                    float shimmer = smoothstep(0.46, 0.78, windWave);
                    float3 rootCol = float3(0.040, 0.130, 0.078);
                    float3 tipCol  = hasVertCol ? i.vertColor.rgb : float3(0.155, 0.380, 0.245);
                    baseRGB = lerp(rootCol, tipCol, smoothstep(0.0, 0.90, tipH));
                    baseRGB = lerp(baseRGB, float3(0.20, 0.48, 0.38), shimmer * tipH * 0.30 * wonder);
                    emission += float3(0.03, 0.11, 0.12) * (tipH * (0.28 + shimmer * 0.72) * 0.22 * wonder);
                }

                float hemiFactor = N.y * 0.5 + 0.5;
                float3 skyAmb = float3(0.50, 0.65, 0.94);
                float3 gndAmb = float3(0.18, 0.24, 0.30);
                float3 hemiLight = lerp(gndAmb, skyAmb, hemiFactor);

                float3 L_moon = normalize(float3(-0.42, 0.78, -0.46));
                float ndotl = max(0.0, dot(N, L_moon));
                float wrapDiff = lerp(ndotl, ndotl * 0.65 + 0.35, 0.42);
                float3 moonLight = float3(0.70, 0.80, 0.98) * (wrapDiff * 0.68);

                float3 V = normalize(_WorldSpaceCameraPos - i.worldPos);
                float rim = pow(1.0 - saturate(dot(N, V)), 2.8);
                // 仅对角色应用暖色晚霞边缘光；草叶与地面采用清澈月华翠绿透射光，避免草叶泛红发枯
                float3 rimTint = (_IsGrass > 0.5 || _IsTerrain > 0.5)
                    ? float3(0.16, 0.46, 0.36) * 0.45
                    : float3(0.92, 0.48, 0.42);
                float3 horizonRim = rimTint * (rim * 0.22 * wonder);

                float3 lit = baseRGB * (hemiLight + moonLight) * _LightMultiplier
                           + horizonRim * _LightMultiplier
                           + emission * _LightMultiplier;

                // 4. 远景大气暮色雾化（在 22m~115m 处柔和过渡到地平线暮光，近处 0~22m 保持 100% 锐利清晰）
                float distFromGate = length(i.worldPos);
                float fogFactor = smoothstep(22.0, 115.0, distFromGate) * saturate(wonder * 0.52);
                if (fogFactor > 0.001)
                {
                    float east = smoothstep(-0.55, 0.50, i.worldPos.x / max(1.0, distFromGate));
                    float3 horizonFogCol = lerp(float3(0.44, 0.22, 0.38), float3(0.14, 0.36, 0.52), east) * _LightMultiplier;
                    lit = lerp(lit, horizonFogCol, fogFactor * 0.68);
                }

                return fixed4(lit, alpha);
            }
            ENDCG
        }
    }
}
