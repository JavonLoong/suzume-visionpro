"""Shared native lighting setup for reviewed trials and the saved candidate."""
import bpy,math
from mathutils import Matrix,Vector
def apply_lighting(s,q):
    sun=bpy.data.objects['DirectionalLight'];position=Vector(q['sunWorldPosition']);sun.matrix_world=Matrix.Translation(position)@(-position).to_track_quat('-Z','Y').to_matrix().to_4x4();sun.data.energy=q['sunEnergy']
    right=bpy.data.objects['Soft courtyard fill on the movie facade v22'];right.location=q['rightPosition'];right.rotation_euler=(Vector(q['rightTarget'])-right.location).to_track_quat('-Z','Y').to_euler();right.data.size=q['rightSize'][0];right.data.size_y=q['rightSize'][1];right.data.energy=q['rightFill'];right.data.color=(1,.92,.82)
    left=bpy.data.objects['Cool courtyard fill on the left facade v23'];left.data.energy=q['leftFill'];left.data.color=q['leftColor'];bpy.data.lights['Localized sunlight around the arched window v23'].energy=q['archSpot']
    nodes=s.world.node_tree.nodes;links=s.world.node_tree.links;bg=nodes.get('Background');bg.inputs['Strength'].default_value=q['worldStrength']
    # Preserve the true directional environment map. Camera/glossy appearance
    # is separately calibrated; this is an explicitly artistic lighting choice.
    for n in list(nodes):
        if n.name.startswith('Film lighting v27 '):nodes.remove(n)
    colorSource=next(l.from_socket for l in links if l.to_node==bg and l.to_socket.name=='Color')
    tint=nodes.new('ShaderNodeMixRGB');tint.name='Film lighting v27 camera sky color';tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*q['skyTint'],1);links.new(colorSource,tint.inputs[1])
    visible=nodes.new('ShaderNodeBackground');visible.name='Film lighting v27 visible sky';visible.inputs['Strength'].default_value=q['skyStrength'];links.new(tint.outputs['Color'],visible.inputs['Color'])
    path=nodes.new('ShaderNodeLightPath');path.name='Film lighting v27 ray categories'
    glossy=nodes.new('ShaderNodeMath');glossy.name='Film lighting v27 reflection sky contribution';glossy.operation='MULTIPLY';glossy.inputs[1].default_value=q.get('glossySkyWeight',.55);links.new(path.outputs['Is Glossy Ray'],glossy.inputs[0])
    factor=nodes.new('ShaderNodeMath');factor.name='Film lighting v27 camera or reflection';factor.operation='MAXIMUM';links.new(path.outputs['Is Camera Ray'],factor.inputs[0]);links.new(glossy.outputs[0],factor.inputs[1])
    mix=nodes.new('ShaderNodeMixShader');mix.name='Film lighting v27 sky and illumination';links.new(factor.outputs[0],mix.inputs[0]);links.new(bg.outputs[0],mix.inputs[1]);links.new(visible.outputs[0],mix.inputs[2]);out=next(n for n in nodes if n.type=='OUTPUT_WORLD');links.new(mix.outputs[0],out.inputs['Surface'])
    bpy.context.view_layer.update()

BASE={'sunWorldPosition':[-35,-10,32],'sunEnergy':1.3,'worldStrength':.075,'skyStrength':.70,'skyTint':[.5,.9,1.7],'glossySkyWeight':.55,
      'rightPosition':[8.5,19.2,5.6],'rightTarget':[8.62559223175,24.1741256714,3.7],'rightSize':[4,3],'rightFill':650,
      'leftFill':96,'leftColor':[.4,.43,1.0],'archSpot':600}
