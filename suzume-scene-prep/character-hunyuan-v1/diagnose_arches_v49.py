from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path('D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/character-hunyuan-v1');o=r/'poster-arches-v49';d=json.loads((o/'arch-geometry-v49.json').read_text());p=json.loads((r/'poster-upper-windows-v48/upper-window-geometry-v48.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(o/'Suzume_dual_scene_arches_v49.blend'));s=bpy.data.scenes['Official poster courtyard v38'];objects=[s.objects[q['name']] for q in d['sourceObjects']]+[s.objects[q['name']] for q in p['members'] if q['kind'] in ['wall','partition']]+[s.objects[q['name']] for q in d['members'] if q['kind'] in ['wall','cornice']]
for ob in objects:
 tree=BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[p.vertices[:] for p in ob.data.polygons],all_triangles=True)
 for q in d['structuralProbeSpecifications']:
  rec=next(r for r in d['arches'] if r['id']==q['archId']);distance=.6 if rec['kind']=='pointed' and rec['reference'][0]<70 else .1;h=tree.ray_cast(Vector(q['point']),Vector(q['direction']),distance)
  if h[0] is not None:print('BLOCKER',q['archId'],ob.name,'face',h[2],'distance',h[3],flush=True)
