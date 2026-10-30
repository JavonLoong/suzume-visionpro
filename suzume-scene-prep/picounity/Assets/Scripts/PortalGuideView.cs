using System.Collections.Generic;
using UnityEngine;

/// Readable world-space guide cards, shared by headset runtime and the offline preview.
public class PortalGuideView : MonoBehaviour
{
    public enum Context { Browse, Ready, Placement }
    readonly Dictionary<string, Texture2D> _textures = new Dictionary<string, Texture2D>();
    Renderer _card, _footer;
    PortalGapReadout _gap;
    bool _visible = true;
    float _opacity = 1f;
    public void Initialize(Camera camera)
    {
        transform.SetParent(camera.transform, false);
        _card = CreateCard("InstructionCard", new Vector3(0,-.40f,1.45f), new Vector3(1.12f,.392f,1));
        _footer = CreateCard("ControllerLegend", new Vector3(0,-.665f,1.45f), new Vector3(1.12f,.101f,1));
        _gap=new GameObject("RayGapReadout").AddComponent<PortalGapReadout>();_gap.Initialize(transform);
    }
    public void ShowRayGap(float gap,bool visible) { if(_gap!=null)_gap.Show(gap,visible); }
    public void Show(string page, bool visible, bool mountain, Context context=Context.Browse)
    {
        _visible = visible;
        bool compact=context!=Context.Browse;
        _card.transform.localPosition=compact ? new Vector3(0,-.50f,1.6f) : new Vector3(0,-.40f,1.45f);
        _card.transform.localScale=compact ? new Vector3(1.12f,.2315f,1) : new Vector3(1.12f,.392f,1);
        SetTexture(_card,(compact ? "compact_" : "")+page);
        string footer=context==Context.Ready ? "footer_ready_" : (context==Context.Placement ? "footer_placement_" : "footer_");
        SetTexture(_footer,footer+(mountain ? "mountain" : "flat"));
        if (!Application.isPlaying) { _card.enabled = visible; _card.sharedMaterial.color = Color.white; }
    }
    void Update()
    {
        if (_card == null) return;
        _opacity = Mathf.MoveTowards(_opacity,_visible ? 1f : 0f,Time.unscaledDeltaTime*7f);
        _card.enabled = _opacity > .005f;
        _card.sharedMaterial.color = new Color(1,1,1,_opacity);
    }
    Renderer CreateCard(string name,Vector3 position,Vector3 scale)
    {
        var go=GameObject.CreatePrimitive(PrimitiveType.Quad);go.name=name;
        if(Application.isPlaying)Destroy(go.GetComponent<Collider>());else DestroyImmediate(go.GetComponent<Collider>());
        go.transform.SetParent(transform,false);go.transform.localPosition=position;go.transform.localScale=scale;
        var renderer=go.GetComponent<Renderer>();renderer.sharedMaterial=new Material(Resources.Load<Material>("DoorMark/MarkLabel"));
        return renderer;
    }
    void SetTexture(Renderer renderer,string name)
    {
        if(renderer==null)return;
        if(!_textures.TryGetValue(name,out var texture)){texture=Resources.Load<Texture2D>("ControllerGuide/"+name);_textures[name]=texture;}
        if(texture!=null&&renderer.sharedMaterial.mainTexture!=texture)renderer.sharedMaterial.mainTexture=texture;
    }
    void OnDestroy()
    {
        foreach(var renderer in new[]{_card,_footer})
            if(renderer!=null&&Application.isPlaying)Destroy(renderer.sharedMaterial);
    }
}
