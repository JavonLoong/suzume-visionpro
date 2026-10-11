"""Remove duplicate triangles and disconnected reconstruction debris."""
import json, trimesh, shutil
from pathlib import Path
H=Path(__file__).parent
result=json.loads((H/'public-generation-result-2.json').read_text(encoding='utf-8'))
source=Path(result[0]['value'])
shutil.copy2(source,H/'Suzume-head-Hunyuan2mv-original.glb')
mesh=trimesh.load(source,force='mesh')
original_faces=len(mesh.faces)
mesh.update_faces(mesh.unique_faces())
unique_faces=len(mesh.faces)
mesh.update_faces(mesh.nondegenerate_faces())
mesh.remove_unreferenced_vertices()
parts=sorted(mesh.split(only_watertight=False),key=lambda p:len(p.faces),reverse=True)
# The second-largest component is a horizontal sliver below the neck. All hair,
# both ears, the neck and the face belong to the largest connected component.
mesh=parts[0]
mesh.export(H/'new-head-clean.glb')
audit={'sourceFaces':original_faces,'uniqueFaces':unique_faces,
       'cleanFaces':len(mesh.faces),'cleanVertices':len(mesh.vertices),
       'componentsKept':1,'discardedComponentFaceCounts':[len(p.faces) for p in parts[1:]],
       'boundsGLTFYUp':mesh.bounds.tolist(),'watertight':bool(mesh.is_watertight)}
(H/'mesh-cleanup.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit),flush=True)
