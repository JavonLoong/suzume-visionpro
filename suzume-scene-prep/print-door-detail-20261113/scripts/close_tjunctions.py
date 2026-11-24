"""Split collinear boundary edges left after removing zero-area FBX triangles."""
import numpy as np
import trimesh

def close_tjunctions(mesh, tolerance=2e-5):
    mesh=mesh.copy()
    for iteration in range(4):
        counts=np.bincount(mesh.edges_unique_inverse)
        edges=mesh.edges_unique[counts==1]
        if not len(edges):break
        ids=np.unique(edges);points=mesh.vertices[ids];splits={}
        for a,b in edges:
            origin=mesh.vertices[a];delta=mesh.vertices[b]-origin;length2=delta@delta
            if length2<1e-16:continue
            t=(points-origin)@delta/length2
            distance=np.linalg.norm(points-origin-t[:,None]*delta,axis=1)
            valid=(distance<tolerance)&(t>1e-7)&(t<1-1e-7)&(ids!=a)&(ids!=b)
            inserted=ids[valid][np.argsort(t[valid])]
            if len(inserted):splits[(a,b)]=inserted.tolist()
        if not splits:break
        vertices=mesh.vertices.tolist();faces=[]
        for face in mesh.faces:
            boundary=[];changed=False
            for a,b in zip(face,np.roll(face,-1)):
                boundary.append(int(a));key=tuple(sorted([a,b]))
                if key in splits:
                    extra=splits[key];boundary.extend(extra if a<b else extra[::-1]);changed=True
            if not changed:faces.append(face.tolist());continue
            center=len(vertices);vertices.append(np.mean(mesh.vertices[face],axis=0).tolist())
            faces.extend([[a,b,center] for a,b in zip(boundary,boundary[1:]+boundary[:1])])
        mesh=trimesh.Trimesh(vertices,faces,process=False)
        mesh.merge_vertices(digits_vertex=7);mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
    return mesh
