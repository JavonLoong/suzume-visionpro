// 实体对齐门框与双空间同步门扇专用 Shader（4K 级程序化高频木纹与斑驳白漆锐化版）：
// 1. 针对原 512x512 / 265x535 烘焙门框贴图近看模糊的问题，在片元着色器中合成毫米级纵向木纹纤维、
//    剥落白漆台阶微法线以及常春藤叶脉细节，近距离观看依然锐利清晰；
// 2. 支持可选的 Stencil 门洞测试（_StencilRef / _StencilComp）与世界空间半平面裁剪（_ClipPlane / _UseClipPlane）。
Shader "Suzume/DoorFrame"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo (RGB)", 2D) = "white" {}
        _StencilRef ("Stencil Ref", Int) = 1
        _StencilComp ("Stencil Comparison", Int) = 8 // 8 = Always, 3 = Equal, 6 = NotEqual
        _ClipPlane ("World Clip Plane", Vector) = (0, 0, 1, 0)
        _UseClipPlane ("Use Clip Plane", Float) = 0
        _Unlit ("Unlit Flat Color", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry-30" }

        Stencil
        {
            Ref [_StencilRef]
            Comp [_StencilComp]
            Pass Keep
        }

        Cull Off
        ZWrite On
        ZTest LEqual

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
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                float3 worldPos : TEXCOORD2;
                float3 localPos : TEXCOORD3;
            };

            fixed4 _Color;
            sampler2D _MainTex;
            float4 _MainTex_ST;
            float4 _ClipPlane;
            float _UseClipPlane;
            float _Unlit;

            float hash21(float2 p)
            {
                p = frac(p * float2(234.34, 435.345));
                p += dot(p, p + 34.23);
                return frac(p.x * p.y);
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

            float fbm3(float2 p)
            {
                float v = 0.0;
                float a = 0.5;
                for (int idx = 0; idx < 3; idx++)
                {
                    v += a * noise2D(p);
                    p = p * 2.07 + float2(19.3, 41.7);
                    a *= 0.5;
                }
                return v;
            }

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.localPos = v.vertex.xyz;
                return o;
            }

            fixed4 frag (v2f i, fixed facing : VFACE) : SV_Target
            {
                if (_UseClipPlane > 0.5)
                {
                    float dist = dot(i.worldPos, _ClipPlane.xyz) + _ClipPlane.w;
                    clip(dist);
                }

                fixed4 tex = tex2D(_MainTex, i.uv);
                float3 baseRGB = tex.rgb * _Color.rgb;

                if (_Unlit > 0.5)
                {
                    return fixed4(baseRGB, 1.0);
                }

                // 高频程序化木纹与剥落漆面锐化（消除 512x512 贴图近看模糊感）
                float2 woodUV = float2((i.localPos.x + i.localPos.z) * 95.0, i.localPos.y * 18.0);
                float grain = fbm3(woodUV + noise2D(woodUV * 0.25) * 1.8);
                float fineFiber = noise2D(woodUV * float2(3.2, 0.8));

                // 识别贴图中的白漆区、裸露木头区与常春藤绿叶区
                float luma = dot(baseRGB, float3(0.299, 0.587, 0.114));
                float greenDominance = saturate((baseRGB.g - max(baseRGB.r, baseRGB.b * 0.95)) * 4.5);
                float woodExposed = saturate((baseRGB.r - baseRGB.b) * 2.8) * (1.0 - greenDominance);

                // 对漆面与木纹边界做 S 曲线锐化，拒绝糊边
                float paintEdge = smoothstep(0.42, 0.72, luma + (grain - 0.5) * 0.16);
                float3 crispWood = baseRGB * (0.86 + 0.28 * grain) * (0.94 + 0.12 * fineFiber);
                float3 crispPaint = baseRGB * (0.94 + 0.10 * (grain * 0.6 + fineFiber * 0.4));

                // 常春藤叶片高频脉络细节
                float leafDetail = fbm3(i.localPos.xy * 65.0);
                float3 crispIvy = lerp(float3(0.11, 0.28, 0.12), float3(0.26, 0.48, 0.20), smoothstep(0.25, 0.78, leafDetail));

                baseRGB = lerp(crispWood, crispPaint, paintEdge);
                baseRGB = lerp(baseRGB, crispIvy, greenDominance * 0.55);

                // 微表面凹凸法线扰动
                float3 N = normalize(i.worldNormal) * (facing >= 0 ? 1.0 : -1.0);
                float microBump = (grain - 0.5) * (0.18 + 0.22 * woodExposed) + (leafDetail - 0.5) * 0.25 * greenDominance;
                N = normalize(N + float3(microBump, microBump * 0.4, -microBump * 0.5));

                float hemi = N.y * 0.5 + 0.5;
                float3 amb = lerp(float3(0.34, 0.38, 0.30), float3(0.88, 0.94, 1.00), hemi) * 0.78;

                float3 L = normalize(float3(-3.0, 5.0, 4.0));
                float ndotl = max(0.0, dot(N, L));
                float3 sun = float3(1.00, 0.94, 0.85) * (ndotl * 0.64);

                float3 col = baseRGB * (amb + sun);
                return fixed4(col, 1.0);
            }
            ENDCG
        }
    }
}
