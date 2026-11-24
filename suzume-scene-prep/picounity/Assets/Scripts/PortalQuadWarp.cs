using System.Collections.Generic;
using UnityEngine;

// Deforms the actual aperture and static frame. The scenery remains rigid behind the aperture.
public sealed class PortalQuadWarp : MonoBehaviour
{
    sealed class Part { public MeshFilter filter; public Mesh original,mesh; public Vector3[] source,target; public Matrix4x4 toRoot,fromRoot; }
    readonly List<Part> parts=new List<Part>();
    Vector3[] last;Transform lastMask,lastFrame;
    public void Apply(Vector3[] corners)
    {
        if(!DoorQuadPlacement.HasFourFiniteCorners(corners))corners=null;
        var mask=transform.Find("PortalMask");var frame=transform.Find("DoorAssembly");
        if(mask!=lastMask||frame!=lastFrame) { Release();last=null;lastMask=mask;lastFrame=frame; }
        if(corners==null&&last==null)return;
        if(corners!=null&&last!=null) { bool same=true;for(int i=0;i<4;i++)same&=(corners[i]-last[i]).sqrMagnitude<1e-8f;if(same)return; }
        if(corners==null) { Release();last=null;return; }
        if(parts.Count==0)
        {
            foreach(var root in new[]{mask,frame})
            {
                if(root==null)continue;
                foreach(var filter in root.GetComponentsInChildren<MeshFilter>(true))
                {
                    if(filter.sharedMesh==null)continue;
                    var p=new Part {filter=filter,original=filter.sharedMesh,mesh=Instantiate(filter.sharedMesh)};
                    p.mesh.name=p.original.name+"_AdjustedOpening";p.source=p.original.vertices;p.target=new Vector3[p.source.Length];
                    p.toRoot=transform.worldToLocalMatrix*filter.transform.localToWorldMatrix;p.fromRoot=p.toRoot.inverse;
                    filter.sharedMesh=p.mesh;parts.Add(p);
                }
            }
        }
        foreach(var p in parts)
        {
            if(p.filter==null)continue;
            for(int i=0;i<p.source.Length;i++)p.target[i]=p.fromRoot.MultiplyPoint3x4(DoorQuadPlacement.Warp(p.toRoot.MultiplyPoint3x4(p.source[i]),corners));
            p.mesh.vertices=p.target;p.mesh.RecalculateBounds();p.mesh.RecalculateNormals();
        }
        last=(Vector3[])corners.Clone();
    }
    void Release()
    {
        foreach(var p in parts) { if(p.filter!=null)p.filter.sharedMesh=p.original;if(p.mesh!=null){if(Application.isPlaying)Destroy(p.mesh);else DestroyImmediate(p.mesh);} }
        parts.Clear();
    }
    void OnDestroy(){Release();}
}
