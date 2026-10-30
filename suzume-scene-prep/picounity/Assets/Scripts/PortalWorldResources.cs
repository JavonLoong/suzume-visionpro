using System.Collections.Generic;
using UnityEngine;

// Release only materials cloned by MaterialMapper and meshes generated for this world's atmosphere.
// Imported FBX meshes and shared texture assets remain owned by Unity.
public class PortalWorldResources : MonoBehaviour
{
    readonly HashSet<Material> _materials = new HashSet<Material>();
    readonly HashSet<Mesh> _meshes = new HashSet<Mesh>();
    public static void Track(GameObject root)
    {
        if (!Application.isPlaying) return;
        var owner = root.AddComponent<PortalWorldResources>();
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
            foreach (var material in renderer.sharedMaterials) if(material != null) owner._materials.Add(material);
        var atmosphere = root.transform.Find(DreamWorldAtmosphere.RootName);
        if (atmosphere != null)
            foreach(var filter in atmosphere.GetComponentsInChildren<MeshFilter>(true))
                if(filter.sharedMesh != null) owner._meshes.Add(filter.sharedMesh);
    }
    void OnDestroy()
    {
        foreach(var material in _materials) if(material != null) Destroy(material);
        foreach(var mesh in _meshes) if(mesh != null) Destroy(mesh);
    }
}
