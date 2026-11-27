using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor.SceneManagement;
using UnityEngine;

// Requirement audit, not a passing occlusion implementation test. The real leaf belongs
// to passthrough, so scene alpha must be zero wherever its projected foreground covers the opening.
public static class PhysicalLeafCoverageAudit
{
    const string Root="D:/suzume-integration-20261127/leaf-occlusion-audit/";
    [Serializable] class Case {public bool leftHinge;public float angle,eye;public int openingPixels,virtualOpeningPixels,requiredClearPixels,incorrectlyCoveredPixels;public float incorrectFraction;}
    [Serializable] class Report {public string scope;public bool physicalLeafOcclusionImplemented;public List<Case> cases=new List<Case>();}
    static bool Inside(Vector2 q,Vector2[] polygon,out float edgeDistance)
    {
        bool positive=false,negative=false;edgeDistance=10000;
        for(int i=0;i<polygon.Length;i++)
        {
            var a=polygon[i];var b=polygon[(i+1)%polygon.Length];var d=b-a;
            if(d.sqrMagnitude<1e-10f)continue;
            float cross=d.x*(q.y-a.y)-d.y*(q.x-a.x);positive|=cross>0;negative|=cross<0;
            edgeDistance=Mathf.Min(edgeDistance,Vector2.Distance(q,a+d*Mathf.Clamp01(Vector2.Dot(q-a,d)/d.sqrMagnitude)));
        }
        return !(positive&&negative);
    }
    static Vector2[] Project(Camera camera,Vector3[] corners)
    {var p=new Vector2[4];int[] ring={0,1,3,2};for(int i=0;i<4;i++)p[i]=camera.WorldToScreenPoint(corners[ring[i]]);return p;}
    public static void Run()
    {
        Directory.CreateDirectory(Root);EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var portal=UnityEngine.Object.FindObjectOfType<PortalManager>();portal.BuildPortal();
        portal.physicalOpeningOnly=true;portal.calibrationHidden=false;portal.useFullRotation=true;portal.portalRotation=Quaternion.identity;
        portal.portalPosition=Vector3.zero;portal.portalWidth=.025f;portal.portalHeight=.06f;
        portal.UpdatePortalState(); // Apply size/pose before converting world corners into local mesh coordinates.
        var opening=DoorQuadPlacement.Rectangle(Vector3.zero,Quaternion.identity,.025f,.06f);portal.SetWorldCorners(opening);portal.UpdatePortalState();
        foreach(var renderer in UnityEngine.Object.FindObjectsOfType<Renderer>())renderer.enabled=false;
        portal.transform.Find("DreamWorld").gameObject.SetActive(false);portal.enabled=false;
        portal.transform.Find("PortalMask").GetComponent<Renderer>().enabled=true;
        var backdrop=GameObject.CreatePrimitive(PrimitiveType.Quad);backdrop.transform.position=new Vector3(0,.03f,-.04f);backdrop.transform.localScale=Vector3.one;
        var material=new Material(Shader.Find("Suzume/PortalTarget"));material.SetColor("_Color",Color.white);material.SetFloat("_Unlit",1);
        material.SetFloat("_WindStrength",0);material.SetFloat("_AtmosphereIntensity",0);material.SetInt("_StencilComp",3);
        material.SetVector("_ClipPlane",portal.ComputeWorldClipPlane());material.SetFloat("_UseClipPlane",1);backdrop.GetComponent<Renderer>().sharedMaterial=material;
        var camera=Camera.main;camera.nearClipPlane=.001f;camera.farClipPlane=3;camera.fieldOfView=42;camera.aspect=1;
        camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;camera.allowMSAA=false;
        var rt=new RenderTexture(512,512,24,RenderTextureFormat.ARGB32);rt.antiAliasing=1;camera.targetTexture=rt;
        var report=new Report{scope="Analytical 25 x 60 mm leaf/opening fixture with actual production portal shaders. Three viewpoints (including +/-32 mm), both hinge sides, four opening angles. Not a physical headset observation."};
        try
        {
            foreach(bool left in new[]{true,false})foreach(float angle in new[]{0f,30f,60f,90f})foreach(float eye in new[]{-.032f,0f,.032f})
            {
                camera.transform.position=new Vector3(eye,.032f,.18f);camera.transform.LookAt(new Vector3(0,.03f,0));camera.Render();
                RenderTexture.active=rt;var image=new Texture2D(512,512,TextureFormat.RGBA32,false);image.ReadPixels(new Rect(0,0,512,512),0,0);image.Apply();var pixels=image.GetPixels32();
                float hinge=left?-.0125f:.0125f,sign=left?1:-1;float x=hinge+sign*.025f*Mathf.Cos(angle*Mathf.Deg2Rad),z=.025f*Mathf.Sin(angle*Mathf.Deg2Rad);
                var leaf=left?new[]{new Vector3(hinge,0,0),new Vector3(x,0,z),new Vector3(hinge,.06f,0),new Vector3(x,.06f,z)}:
                    new[]{new Vector3(x,0,z),new Vector3(hinge,0,0),new Vector3(x,.06f,z),new Vector3(hinge,.06f,0)};
                var aperturePixels=Project(camera,opening);var leafPixels=Project(camera,leaf);var row=new Case{leftHinge=left,angle=angle,eye=eye};
                for(int py=0;py<512;py++)for(int px=0;px<512;px++)
                {
                    var q=new Vector2(px+.5f,py+.5f);
                    if(!Inside(q,aperturePixels,out float da)||da<2)continue;
                    row.openingPixels++;if(pixels[py*512+px].a>240)row.virtualOpeningPixels++;
                    if(!Inside(q,leafPixels,out float dl)||dl<2)continue;
                    row.requiredClearPixels++;if(pixels[py*512+px].a>240)row.incorrectlyCoveredPixels++;
                }
                row.incorrectFraction=row.requiredClearPixels==0?0:row.incorrectlyCoveredPixels/(float)row.requiredClearPixels;report.cases.Add(row);
                if(row.openingPixels<1000||row.virtualOpeningPixels<row.openingPixels*.99f)
                    throw new Exception("Invalid audit setup: the virtual background did not fill the reference aperture.");
                if(left&&angle==60f&&eye==-.032f)
                {
                    File.WriteAllBytes(Root+"actual-alpha.png",image.EncodeToPNG());
                    var reference=new Color32[512*512];
                    for(int py=0;py<512;py++)for(int px=0;px<512;px++)
                    {
                        var q=new Vector2(px+.5f,py+.5f);
                        bool aperture=Inside(q,aperturePixels,out float ignoredA);
                        bool leafHit=Inside(q,leafPixels,out float ignoredL);
                        reference[py*512+px]=aperture&&!leafHit?new Color32(255,255,255,255):new Color32(0,0,0,0);
                    }
                    image.SetPixels32(reference);image.Apply();
                    File.WriteAllBytes(Root+"required-alpha.png",image.EncodeToPNG());
                }
                UnityEngine.Object.DestroyImmediate(image);
            }
        }
        finally{camera.targetTexture=null;RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(rt);}
        report.physicalLeafOcclusionImplemented=report.cases.TrueForAll(c=>c.incorrectlyCoveredPixels==0);
        File.WriteAllText(Root+"coverage-audit.json",JsonUtility.ToJson(report,true));
        int covered=0,required=0;foreach(var c in report.cases){covered+=c.incorrectlyCoveredPixels;required+=c.requiredClearPixels;}
        string summary=$"OBSERVED_REQUIREMENT_GAP: {covered}/{required} tested foreground-leaf pixels were covered by virtual content across {report.cases.Count} analytical views. No field measurement. Current whole-opening mask does not implement real-leaf occlusion.";
        File.WriteAllText(Root+"coverage-audit.txt",summary+"\n");Debug.Log("[PhysicalLeafCoverageAudit] "+summary);
    }
}
