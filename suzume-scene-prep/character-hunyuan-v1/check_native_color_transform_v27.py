"""Small isolated render validates inverse OCIO values without altering the scene."""
from pathlib import Path
import bpy,json,sys
R=Path(__file__).parent;O=R/'movie-lighting-v27';diagnosis=json.loads((O/'color-transform-diagnosis-v27.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.use_denoising=False;s.render.resolution_x=8;s.render.resolution_y=8;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='None';s.view_settings.exposure=.8;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
camera=bpy.data.objects.new('Color test camera',bpy.data.cameras.new('Color test camera'));s.collection.objects.link(camera);s.camera=camera
world=bpy.data.worlds.new('Isolated color test world');world.use_nodes=True;s.world=world;bg=world.node_tree.nodes['Background'];bg.inputs['Strength'].default_value=1
linked='--linked-sky' in sys.argv
rows=json.loads((O/'native-color-test-v27.json').read_text())['samples'] if linked else []
for name in ([] if linked else ['left shaded wall','clear sky']):
    q=next(q for q in diagnosis['samples'] if q['patch']==name);bg.inputs['Color'].default_value=(*q['inverseSceneLinear'],1);s.render.filepath=str(O/('color-test-'+name.replace(' ','-')+'.png'));bpy.ops.render.render(write_still=True);rows.append({'patch':name,'requestedLinear':q['inverseSceneLinear'],'actualSocketLinear':list(bg.inputs['Color'].default_value[:3]),'targetSrgb255':q['targetSrgb255'],'image':Path(s.render.filepath).name})
if linked:
    q=next(q for q in diagnosis['samples'] if q['patch']=='clear sky');vec=world.node_tree.nodes.new('ShaderNodeCombineXYZ')
    for inp,value in zip(vec.inputs,q['inverseSceneLinear']):inp.default_value=value
    world.node_tree.links.new(vec.outputs[0],bg.inputs['Color']);s.render.filepath=str(O/'color-test-clear-sky-linked.png');bpy.ops.render.render(write_still=True)
    rows.append({'patch':'clear sky via signed vector node','requestedLinear':q['inverseSceneLinear'],'actualLinkedLinear':[inp.default_value for inp in vec.inputs],'targetSrgb255':q['targetSrgb255'],'image':Path(s.render.filepath).name})
(O/'native-color-test-v27.json').write_text(json.dumps({'scope':'Isolated 8x8 constant-world swatches, not a complete scene appearance test.','samples':rows},indent=2),encoding='utf-8');print('NATIVE_COLOR_SWATCHES_RENDERED',flush=True)
