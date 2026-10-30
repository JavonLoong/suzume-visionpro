using System.Globalization;
using UnityEngine;

// A tiny atlas keeps the live centimeter readout crisp without depending on device fonts.
public sealed class PortalGapReadout : MonoBehaviour
{
    readonly Mesh[] _meshes=new Mesh[6];
    readonly Renderer[] _digits=new Renderer[6];
    Material _backgroundMaterial,_digitMaterial;
    int _lastTenths=-1;
    public void Initialize(Transform parent)
    {
        transform.SetParent(parent,false);transform.localPosition=new Vector3(0,-.30f,1.58f);
        var template=Resources.Load<Material>("DoorMark/MarkLabel");
        var panel=GameObject.CreatePrimitive(PrimitiveType.Quad);panel.name="GapReadoutBackground";
        Release(panel.GetComponent<Collider>());panel.transform.SetParent(transform,false);panel.transform.localScale=new Vector3(.65f,.106f,1);
        _backgroundMaterial=new Material(template);_backgroundMaterial.mainTexture=Resources.Load<Texture2D>("ControllerGuide/gap_label");
        panel.GetComponent<Renderer>().sharedMaterial=_backgroundMaterial;
        _digitMaterial=new Material(template);_digitMaterial.mainTexture=Resources.Load<Texture2D>("ControllerGuide/gap_digits");
        _digitMaterial.renderQueue=4001;
        for(int i=0;i<6;i++)
        {
            var go=new GameObject("GapDigit"+i);go.transform.SetParent(transform,false);
            go.transform.localPosition=new Vector3(-.06f+i*.046f,0,-.002f);go.transform.localScale=new Vector3(.054f,.081f,1);
            var mesh=new Mesh { name="GapDigitQuad" };
            mesh.vertices=new[]{new Vector3(-.5f,-.5f,0),new Vector3(.5f,-.5f,0),new Vector3(.5f,.5f,0),new Vector3(-.5f,.5f,0)};
            mesh.triangles=new[]{0,2,1,0,3,2};mesh.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};mesh.RecalculateBounds();
            go.AddComponent<MeshFilter>().sharedMesh=mesh;_meshes[i]=mesh;
            _digits[i]=go.AddComponent<MeshRenderer>();_digits[i].sharedMaterial=_digitMaterial;
        }
        gameObject.SetActive(false);
    }
    public void Show(float gap,bool visible)
    {
        gameObject.SetActive(visible);
        if(!visible||_digitMaterial==null)return;
        _digitMaterial.color=new Color(.3f,1f,.6f);
        int tenths=Mathf.Clamp(Mathf.RoundToInt(gap*1000f),0,99999);
        if(tenths==_lastTenths)return;
        _lastTenths=tenths;
        string value=(tenths/10f).ToString("0.0",CultureInfo.InvariantCulture).PadLeft(6);
        for(int i=0;i<6;i++)
        {
            char c=value[i];_digits[i].enabled=c!=' ';
            if(c==' ')continue;
            int index=c=='.' ? 10 : c-'0';float left=index/11f,right=(index+1)/11f;
            _meshes[i].uv=new[]{new Vector2(left,0),new Vector2(right,0),new Vector2(right,1),new Vector2(left,1)};
        }
    }
    static void Release(Object obj) { if(obj==null)return;if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj); }
    void OnDestroy() { foreach(var mesh in _meshes)Release(mesh);Release(_backgroundMaterial);Release(_digitMaterial); }
}
