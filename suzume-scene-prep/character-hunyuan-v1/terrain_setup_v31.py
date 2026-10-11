"""Editable terrain continuation and finite low-lying three-dimensional mist."""
from pathlib import Path
import bpy,numpy as np,json
from mathutils import Matrix,Vector
from night_setup_v30 import Nodes
R=Path(__file__).parent;O=R/'movie-terrain-v31'

def fog_material(ob,row,q):
    m=ob.data.materials[0];m.use_nodes=True;tree=m.node_tree;tree.nodes.clear();n=Nodes(tree);op=n.op
    tc=n.nodes.new('ShaderNodeTexCoord');split=n.nodes.new('ShaderNodeSeparateXYZ');n.links.new(tc.outputs['Generated'],split.inputs[0]);p=[op('SUBTRACT',op('MULTIPLY',split.outputs[k],2),1) for k in ['X','Y','Z']]
    x,y,z=[op('ADD',op('MULTIPLY',p[i],row['halfSize'][i]),row['center'][i]) for i in range(3)]
    phase=op('ADD',op('ADD',op('MULTIPLY',x,.08),op('MULTIPLY',y,.10)),row['seed'])
    center=op('ADD',row['center'][2],op('MULTIPLY',op('SINE',phase),.13));h=op('DIVIDE',op('SUBTRACT',z,center),row['halfSize'][2]*.38)
    vertical=op('EXPONENT',op('MULTIPLY',op('MULTIPLY',h,h),-2))
    wind=op('MULTIPLY',op('SINE',op('ADD',op('ADD',op('MULTIPLY',x,.17),op('MULTIPLY',y,.11)),row['seed'])),op('SINE',op('SUBTRACT',op('MULTIPLY',x,.043),op('MULTIPLY',y,.07))))
    flow=op('ADD',.65,op('MULTIPLY',wind,.35));edge=op('MAXIMUM',op('MAXIMUM',op('ABSOLUTE',p[0]),op('ABSOLUTE',p[1])),op('ABSOLUTE',p[2]));fade=op('SUBTRACT',1,n.smooth(.7,1,edge))
    lateral=n.smooth(*q.get('fogLateralX',[-7,4]),x)
    gains=q.get('fogLateralGain',[1,1]);gain=op('ADD',gains[0],op('MULTIPLY',lateral,gains[1]-gains[0]))
    density=op('MULTIPLY',op('MULTIPLY',op('MULTIPLY',op('MULTIPLY',vertical,flow),fade),gain),q['fogDensity']*row['weight'],'Low mist density v31')
    volume=n.nodes.new('ShaderNodeVolumePrincipled');volume.name='Low spatial mist v31';volume.inputs['Color'].default_value=(.05,.055,.10,1);volume.inputs['Anisotropy'].default_value=.15
    left=q.get('fogLeftLinear',q['fogColorLinear']);right=q.get('fogRightLinear',q['fogColorLinear'])
    color=n.xyz(*[op('ADD',a,op('MULTIPLY',lateral,b-a)) for a,b in zip(left,right)])
    n.links.new(density,volume.inputs['Density']);n.links.new(color,volume.inputs['Emission Color']);n.links.new(op('MULTIPLY',density,q['fogEmissionGain'],'Low mist emission v31'),volume.inputs['Emission Strength'])
    out=n.nodes.new('ShaderNodeOutputMaterial');n.links.new(volume.outputs[0],out.inputs['Volume']);m['spatial_mist_revision']=31;m['reference_image_used']=False

def apply_terrain(q):
    realm=bpy.data.collections['Editable night realm'];ground=bpy.data.objects['Rolling meadow ground'];world=np.fromfile(O/'ground-world-v31.bin',dtype='<f4').reshape(-1,3);mask=np.hypot(world[:,0],world[:,1])>q['unchangedNearRadius'];inv=np.array(ground.matrix_world.inverted());local=world@inv[:3,:3].T+inv[:3,3]
    for i in np.where(mask)[0]:ground.data.vertices[int(i)].co=local[i]
    ground.data.update();ground['distant_terrain_revision']=31
    v=np.fromfile(O/'extension-vertices-v31.bin',dtype='<f4').reshape(-1,3);f=np.fromfile(O/'extension-indices-v31.bin',dtype='<u4').reshape(-1,3)
    mesh=bpy.data.meshes.new('Closed continuous far meadow v31');mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.use_smooth=poly.center.z>-50
        for loop in poly.loop_indices:
            co=mesh.vertices[mesh.loops[loop].vertex_index].co;uv.data[loop].uv=((co.x+200)/400,(co.y+200)/400)
    extension=bpy.data.objects.new('Continuous distant meadow v31',mesh);realm.objects.link(extension);mesh.materials.append(ground.data.materials[0]);extension['terrain_revision']=31;extension['hidden_geometry_inferred']=True
    fogs=[]
    for i,row in enumerate(q['fogVolumes']):
        verts=[(x,y,z) for x in [-1,1] for y in [-1,1] for z in [-1,1]];faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
        me=bpy.data.meshes.new('Mist volume enclosure '+str(i));me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Low meadow mist v31 '+str(i),me);realm.objects.link(ob);ob.matrix_world=Matrix.Translation(Vector(row['center']))@Matrix.Diagonal((*row['halfSize'],1));ob.visible_shadow=False
        mat=bpy.data.materials.new(ob.name);me.materials.append(mat);fog_material(ob,row,q);ob['mist_revision']=31;ob['density_field']='Finite height-varying Gaussian mist with three-dimensional wind modulation';fogs.append(ob)
    bpy.context.view_layer.update();return ground,extension,fogs
