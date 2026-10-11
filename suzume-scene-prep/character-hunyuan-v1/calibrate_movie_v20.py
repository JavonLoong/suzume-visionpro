"""Movie-opening courtyard variant; v19 poster geometry remains on disk.

Fit the full circular building instead of moving camera-facing pieces. Extend
the existing ground story continuously to the water bed: an affine Z offset
alone would leave the entire hotel floating. Near-door objects stay fixed.
"""
from pathlib import Path
import bpy,json,math,sys,hashlib,numpy as np
from mathutils import Matrix,Vector,Euler
R=Path(__file__).parent;O=R/'movie-calibration-v20'
fit=json.loads((O/'courtyard-fit-v20.json').read_text());p=fit['parameters']
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
xy=Matrix.Translation((p['translateX'],p['translateY'],0))@Matrix.Rotation(-p['yaw'],4,'Z')
rot=np.array(xy)[:3,:3];trans=np.array(xy)[:3,3]
depth_scale=fit.get('depthScale',1.0);cam=np.array(fit.get('depthScaleCenter',[.18,-4.039798,1.980399]))
depth_xy=Matrix.Translation(tuple(cam))@Matrix.Diagonal((depth_scale,depth_scale,1,1))@Matrix.Translation(tuple(-cam))
changes=[]

def hotel_height(z):
    # Keep the floor grounded. The facade fit starts at the window sill 1.22m.
    # Below .89m, stretch the solid podium and walls down to the existing bed.
    join=.89;bottom=-.22;top=cam[2]+depth_scale*(join*p['heightScale']+p['heightOffset']-cam[2])
    upper=cam[2]+depth_scale*(z*p['heightScale']+p['heightOffset']-cam[2])
    return np.where(z>=join,upper,bottom+(z-bottom)*(top-bottom)/(join-bottom))

def edit_mesh(o,kind):
    M=np.array(o.matrix_world);inv=np.linalg.inv(M)
    a=np.empty((len(o.data.vertices),3),np.float64);o.data.vertices.foreach_get('co',a.ravel())
    world=a@M[:3,:3].T+M[:3,3];radius=np.linalg.norm(world[:,:2],axis=1)
    mask=radius>8 if kind in ['ivy','rubble'] else np.ones(len(a),dtype=bool)
    moved=world[mask]@rot.T+trans
    moved[:,:2]=cam[:2]+depth_scale*(moved[:,:2]-cam[:2])
    moved[:,2]*=depth_scale
    if kind in ['hotel','ivy']:
        heights=world[mask,2]
        if kind=='hotel':
            # Furniture inside the colonnade keeps its original water-level seat.
            # Structural walls/platforms lie beyond 22.5m; selected vertices all
            # share their original topology, attributes and materials.
            # Smooth the courtyard-facing stair transition instead of creating
            # a vertical discontinuity through triangles at a radial threshold.
            blend=np.clip((radius[mask]-21.7)/.8,0,1);blend=blend*blend*(3-2*blend)
            moved[:,2]=heights*depth_scale*(1-blend)+hotel_height(heights)*blend
        else:moved[:,2]=hotel_height(heights)
    world[mask]=moved
    result=world@inv[:3,:3].T+inv[:3,3]
    o.data=o.data.copy();o.data.vertices.foreach_set('co',result.astype('f4').ravel());o.data.update()
    # Custom split normals belong to the old orientation. Recompute from solids.
    if not o.modifiers:
        try:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        except Exception:pass
    if kind=='ivy':
        attr=o.data.attributes.get('instance_rotation')
        if attr:
            local_rot=Matrix.Rotation(-p['yaw'],4,'Y')
            for i in np.flatnonzero(mask):
                v=attr.data[int(i)].vector
                e=(local_rot@Euler(v,'XYZ').to_matrix().to_4x4()).to_euler('XYZ')
                attr.data[int(i)].vector=e
        scales=o.data.attributes.get('instance_scale')
        if scales:
            for i in np.flatnonzero(mask):scales.data[int(i)].vector*=depth_scale
    changes.append({'object':o.name,'operation':kind,'verticesMoved':int(mask.sum()),'verticesKept':int((~mask).sum())})

for o in list(s.objects):
    n=o.name
    if n.startswith('Circular ruined hotel with exterior entrance solid mesh'):edit_mesh(o,'hotel')
    elif n.startswith('Broken radial dome steelwork solid mesh'):
        # Scale all steel members coherently, with their original feet on water.
        depth_z=Matrix.Diagonal((1,1,depth_scale,1))
        o.matrix_world=depth_z@depth_xy@xy@o.matrix_world;changes.append({'object':n,'operation':'full courtyard placement and uniform depth scale'})
    elif n.startswith('Brick and masonry debris solid mesh'):edit_mesh(o,'rubble')
    elif n=='Individual three-dimensional ivy leaves':edit_mesh(o,'ivy')
    elif n in ['Branching tree crowns surrounding the ruined hotel','Forest trunks','Continuous forest terrain']:
        o.matrix_world=Matrix.Diagonal((1,1,depth_scale,1))@depth_xy@xy@o.matrix_world;changes.append({'object':n,'operation':'uniformly scaled environment with attached tree roots'})
    elif n=='Live planar reflective shallow water':
        o.matrix_world=depth_xy@xy@o.matrix_world;changes.append({'object':n,'operation':'courtyard placement; water stays horizontal'})

# Extend the basin bed while retaining the original, human-scale paving under
# the door. The broad outer bed is subordinate to the existing real flagstones.
bed=bpy.data.objects['Flooded polygon flagstones and broken slabs solid mesh'].copy();bed.data=bed.data.copy();bed.name='Movie courtyard continuous basin bed';s.collection.objects.link(bed)
bed.matrix_world=depth_xy@xy@bed.matrix_world
bed_matrix=bed.matrix_world.copy();bed_matrix.translation.z-=.04;bed.matrix_world=bed_matrix

bpy.context.view_layer.update()
body=bpy.data.objects['Suzume Hunyuan textured surface'];e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(body.matrix_world);a=a@M[:3,:3].T+M[:3,3];e.to_mesh_clear()
fingerprint=hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
assert fingerprint=='bda994f4f36c980ac7e48122ea45f395ce5defbd723d5c82f514aeca5561de47'
audit={'revision':20,'variant':'movie-opening','fitParameters':p,'depthScale':depth_scale,'courtyardRadiusMeters':23.5*depth_scale,'changes':changes,'bodyWorldHash':fingerprint,'bodyAndFootClearancesPreserved':True,'posterSourcePreserved':'Suzume_scene_Hunyuan_v19.blend','oneToOneComplete':False,'visuallyReviewed':False,'limitations':['Movie bay types and individual window dimensions still require correction.','The lower podium and architectural scale are inferred; the waterline fit is intentionally incomplete.','Front reference camera and character stay at v19 settings.']}
s['courtyard_variant']='Movie-opening calibration v20'
s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_candidate_v20.blend'))
(O/'integration-v20.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('MOVIE_COURTYARD_CANDIDATE_SAVED',json.dumps(audit),flush=True)
if '--render' in sys.argv:
    s.render.filepath=str(O/'movie-front-candidate-v20.png');bpy.ops.render.render(write_still=True)
