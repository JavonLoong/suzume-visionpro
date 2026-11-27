using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor.SceneManagement;
using UnityEngine;

// Offscreen raster verification of the real application mask and target shaders.
public static class PhysicalApertureTrialCheck
{
    const string Output="D:/suzume-aperture-fit-20261125";
    static void Require(bool ok,string message){if(!ok)throw new Exception(message);}
    public static void Run()
    {
        Directory.CreateDirectory(Output);
        PhysicalDoorTrialCheck.Run();
        EditorSceneManager.OpenScene("Assets/Scenes/SuzumePortal.unity");
        var p=UnityEngine.Object.FindObjectOfType<PortalManager>();p.BuildPortal();
        p.physicalOpeningOnly=true;p.calibrationHidden=false;p.portalPosition=Vector3.zero;
        p.portalHeight=.06f;p.portalWidth=.025f;p.useFullRotation=true;p.portalRotation=Quaternion.identity;
        p.fullMeadowView=true;p.frameMode=PortalConfig.FrameMode.Reference;p.showDoorLeaf=true;
        p.UpdatePortalState();
        var mask=p.transform.Find("PortalMask");
        Require(mask.gameObject.activeSelf,"legacy full-view preference disabled physical aperture");
        Require(!p.transform.Find("DoorAssembly").gameObject.activeSelf,"replacement frame still visible");
        var cam=Camera.main;
        cam.transform.position=new Vector3(0,.03f,-.01f);p.UpdatePortalState();
        Require(mask.gameObject.activeSelf,"crossing door disabled clipping");
        foreach(var renderer in p.GetComponentsInChildren<Renderer>(true))
        foreach(var mat in renderer.sharedMaterials)
            if(renderer.gameObject.activeInHierarchy&&mat!=null&&mat.shader.name=="Suzume/PortalTarget")
                Require(mat.GetInt("_StencilComp")==3,"scenery bypasses inner aperture");

        // Isolate the two production shaders, keeping the production warped mask geometry.
        foreach(var renderer in UnityEngine.Object.FindObjectsOfType<Renderer>())renderer.enabled=false;
        p.transform.Find("DreamWorld").gameObject.SetActive(false);
        p.enabled=false;
        mask.GetComponent<Renderer>().enabled=true;
        var backdrop=GameObject.CreatePrimitive(PrimitiveType.Quad);
        backdrop.transform.position=new Vector3(0,.03f,-.04f);backdrop.transform.localScale=Vector3.one*2;
        var material=new Material(Shader.Find("Suzume/PortalTarget"));
        material.SetColor("_Color",Color.white);material.SetFloat("_Unlit",1);material.SetFloat("_WindStrength",0);
        material.SetFloat("_AtmosphereIntensity",0);material.SetInt("_StencilComp",3);
        material.SetVector("_ClipPlane",p.ComputeWorldClipPlane());material.SetFloat("_UseClipPlane",1);
        backdrop.GetComponent<Renderer>().sharedMaterial=material;
        var translucent=GameObject.CreatePrimitive(PrimitiveType.Quad);
        translucent.transform.position=new Vector3(0,.03f,-.02f);translucent.transform.localScale=Vector3.one*2;
        var translucentMaterial=new Material(material);translucentMaterial.SetFloat("_Alpha",.35f);
        translucentMaterial.renderQueue=2011;translucent.GetComponent<Renderer>().sharedMaterial=translucentMaterial;
        cam.nearClipPlane=.001f;cam.farClipPlane=3;cam.fieldOfView=42;cam.aspect=1;
        cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.clear;cam.allowMSAA=false;
        var rt=new RenderTexture(640,640,24,RenderTextureFormat.ARGB32);rt.antiAliasing=1;cam.targetTexture=rt;
        var report=new List<string>();
        try
        {
            foreach(bool warped in new[]{false,true})
            {
                var points=DoorQuadPlacement.Rectangle(Vector3.zero,Quaternion.identity,.025f,.06f);
                if(warped){points[2]+=new Vector3(.002f,-.001f,.002f);points[3]+=new Vector3(-.001f,.001f,-.001f);}
                p.SetWorldCorners(points);
                foreach(float side in new[]{0f,-.035f,.035f})
                {
                    cam.transform.SetPositionAndRotation(new Vector3(side,.032f,.13f),Quaternion.identity);
                    cam.transform.LookAt(new Vector3(0,.03f,0));
                    cam.Render();RenderTexture.active=rt;
                    var image=new Texture2D(640,640,TextureFormat.RGBA32,false);
                    image.ReadPixels(new Rect(0,0,640,640),0,0);image.Apply();
                    var pixels=image.GetPixels32();var ring=new[]{0,1,3,2};var screen=new Vector2[4];
                    for(int i=0;i<4;i++)screen[i]=cam.WorldToScreenPoint(points[ring[i]]);
                    int gap=0,spill=0,inside=0,outside=0;
                    for(int y=0;y<640;y++)for(int x=0;x<640;x++)
                    {
                        var q=new Vector2(x+.5f,y+.5f);bool pos=false,neg=false;float distance=10000;
                        for(int i=0;i<4;i++)
                        {
                            var a=screen[i];var b=screen[(i+1)%4];var edge=b-a;
                            float cross=edge.x*(q.y-a.y)-edge.y*(q.x-a.x);
                            pos|=cross>0;neg|=cross<0;
                            distance=Mathf.Min(distance,Vector2.Distance(q,a+edge*Mathf.Clamp01(Vector2.Dot(q-a,edge)/edge.sqrMagnitude)));
                        }
                        if(distance<2)continue; // Exclude raster edge coverage, not an application inset.
                        bool covered=pixels[y*640+x].a>240;
                        if(!(pos&&neg)){inside++;if(!covered)gap++;}else{outside++;if(covered)spill++;}
                    }
                    string name=(warped?"adjusted":"rectangle")+"_"+side.ToString("F3",System.Globalization.CultureInfo.InvariantCulture);
                    report.Add(name+" inside="+inside+" outside="+outside+" gap="+gap+" spill="+spill);
                    File.WriteAllBytes(Output+"/"+name+".png",image.EncodeToPNG());UnityEngine.Object.DestroyImmediate(image);
                    Require(inside>1000&&gap==0&&spill==0,"aperture pixel coverage failed: "+report[report.Count-1]);
                    var unchanged=p.GetWorldCorners();for(int i=0;i<4;i++)Require(Vector3.Distance(unchanged[i],points[i])<1e-6f,"head movement moved aperture");
                }
            }
        }
        finally {cam.targetTexture=null;RenderTexture.active=null;UnityEngine.Object.DestroyImmediate(rt);}
        File.WriteAllLines(Output+"/aperture-check.txt",report);
        Debug.Log("[PhysicalApertureTrialCheck] ALL CHECKS PASSED: six raster views, no interior gaps or outside spill beyond 2px raster boundary; controller/save regression passed. PC only.");
    }
}
