// 实体门框/门扇遮挡 Shader（对应 Vision Pro 的 OcclusionMaterial）：
// 不输出任何颜色（透视模式下直接露出真实世界的实体门框），
// 但写入深度并把被门框挡住区域的 Stencil 重置为 0，确保从侧面看时门框厚度能正确遮挡门内花海。
Shader "Suzume/DoorOcclusion"
{
    Properties
    {
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "Queue" = "Geometry-40" }

        ColorMask 0
        ZWrite On
        Cull Off

        Stencil
        {
            Ref 0
            Comp Always
            Pass Replace
        }

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata { float4 vertex : POSITION; };
            struct v2f { float4 pos : SV_POSITION; };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                return fixed4(0, 0, 0, 0);
            }
            ENDCG
        }
    }
}
