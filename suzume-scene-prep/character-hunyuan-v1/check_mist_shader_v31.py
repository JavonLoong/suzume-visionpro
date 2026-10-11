"""Small native fog render to isolate material compiler failures from the full realm."""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-terrain-v31';sys.path.insert(0,str(R));from terrain_setup_v31 import fog_material
q=json.loads((O/'terrain-spec-v31.json').read_text(encoding='utf-8'));bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=1;s.render.resolution_x=48;s.render.resolution_y=48;s.render.resolution_percentage=100;s.render.film_transparent=False
bpy.ops.mesh.primitive_cube_add();ob=bpy.context.object;ob.data.materials.append(bpy.data.materials.new('Isolated mist'));row=dict(q['fogVolumes'][0],center=[0,0,0],halfSize=[1,1,1]);fog_material(ob,row,q)
bpy.ops.object.camera_add(location=(0,-4,.4));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam;s.render.filepath=str(O/'isolated-mist-shader-v31.png');bpy.ops.render.render(write_still=True);print('ISOLATED_MIST_SHADER_RENDERED',flush=True)
