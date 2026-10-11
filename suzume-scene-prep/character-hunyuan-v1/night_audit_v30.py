"""Geometry and material fingerprints used by the native night scene audit."""
import bpy,json,hashlib,numpy as np

def fingerprint(ob,evaluated=False,world=True):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else ob;m=e.to_mesh() if evaluated else ob.data
    v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel())
    if world:
        M=np.array(ob.matrix_world);v=v@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(v,6).astype('<f4').tobytes()).hexdigest()

def topology(ob):
    m=ob.data;indices=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',indices);counts=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',counts)
    return hashlib.sha256(indices.astype('<i4').tobytes()+counts.astype('<i4').tobytes()).hexdigest()

def material_digest(mat):
    if not mat.node_tree:return None
    def value(socket):
        v=getattr(socket,'default_value',None)
        if v is None or isinstance(v,(str,float,int,bool)):return v
        if hasattr(v,'name'):return v.name
        return list(v)
    rows=[]
    for n in sorted(mat.node_tree.nodes,key=lambda n:n.name):
        row={'name':n.name,'type':n.bl_idname,'inputs':[(i.name,value(i)) for i in n.inputs]}
        for key in ['operation','blend_type','interpolation','noise_dimensions','distribution','component','use_clamp']:
            if hasattr(n,key):row[key]=getattr(n,key)
        if n.type in ['VALUE','RGB']:row['outputs']=[value(i) for i in n.outputs]
        if getattr(n,'image',None):row['image']=n.image.name
        if getattr(n,'node_tree',None):row['group']=n.node_tree.name
        rows.append(row)
    links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in mat.node_tree.links)
    return hashlib.sha256(json.dumps([rows,links],sort_keys=True).encode()).hexdigest()

def closed_mesh(ob):
    # Imported cubes have per-face vertices; weld only for this topology audit.
    coords=[tuple(round(x,6) for x in v.co) for v in ob.data.vertices];edges={}
    for p in ob.data.polygons:
        indices=list(p.vertices)
        for a,b in zip(indices,indices[1:]+indices[:1]):
            edge=tuple(sorted((coords[a],coords[b])));edges[edge]=edges.get(edge,0)+1
    return len(set(coords)),all(n==2 for n in edges.values())
