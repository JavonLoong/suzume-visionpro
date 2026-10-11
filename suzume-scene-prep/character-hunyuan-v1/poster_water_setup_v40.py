"""Editable world-space poster water; live scene reflection and refraction.

The shallow-body term is a surface approximation to scattered light, not a
bounded volume simulation. It contains no reference-image texture or camera UV.
"""
def apply_water(scene, q):
    import bpy, json
    water=next(o for o in scene.objects if o.name.startswith('Live planar reflective shallow water'))
    mat=water.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
    def node(kind,name):
        n=nodes.new(kind);n.name=name;n.label=name;return n
    def feed(v,socket):
        if isinstance(v,(float,int)):socket.default_value=v
        else:links.new(v,socket)
    def op(kind,a,b=None,name=None):
        n=node('ShaderNodeMath',name or kind);n.operation=kind;feed(a,n.inputs[0])
        if b is not None:feed(b,n.inputs[1])
        return n.outputs[0]
    geo=node('ShaderNodeNewGeometry','Water world coordinates v40')
    xyz=node('ShaderNodeSeparateXYZ','World XYZ v40');links.new(geo.outputs['Position'],xyz.inputs[0])
    time=node('ShaderNodeValue','Wave time v40');time.outputs[0].default_value=0
    time.outputs[0].driver_add('default_value').driver.expression='(frame-1)/24'
    noise=node('ShaderNodeTexNoise','Irregular wave phase v40');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=.43;noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.65;links.new(geo.outputs['Position'],noise.inputs['Vector'])
    phase_noise=op('MULTIPLY',op('SUBTRACT',noise.outputs['Fac'],.5),q['phaseNoise'])
    amplitude_noise=op('ADD',.45,op('MULTIPLY',noise.outputs['Fac'],1.1))
    height=0
    for i,(ky,kx,speed,amplitude) in enumerate(q['waves']):
        phase=op('ADD',op('MULTIPLY',xyz.outputs['Y'],-ky),op('MULTIPLY',xyz.outputs['X'],kx))
        phase=op('ADD',op('ADD',phase,phase_noise),op('MULTIPLY',time.outputs[0],speed))
        h=op('MULTIPLY',op('MULTIPLY',op('SINE',phase),amplitude),amplitude_noise,'Wave height '+str(i+1)+' v40')
        height=h if i==0 else op('ADD',height,h)
    bump=node('ShaderNodeBump','Irregular millimeter ripples v40');bump.inputs['Distance'].default_value=1;bump.inputs['Strength'].default_value=1;links.new(height,bump.inputs['Height'])
    reflect=node('ShaderNodeBsdfPrincipled','Live poster reflection v40');reflect.inputs['Base Color'].default_value=(*q['reflectionTint'],1);reflect.inputs['Metallic'].default_value=1;reflect.inputs['Roughness'].default_value=q['reflectionRoughness'];links.new(bump.outputs['Normal'],reflect.inputs['Normal'])
    refract=node('ShaderNodeBsdfRefraction','Live submerged stone refraction v40');refract.inputs['Color'].default_value=(*q['transmissionTint'],1);refract.inputs['IOR'].default_value=1.333;refract.inputs['Roughness'].default_value=q['transmissionRoughness'];links.new(bump.outputs['Normal'],refract.inputs['Normal'])
    dot=node('ShaderNodeVectorMath','View cosine v40');dot.operation='DOT_PRODUCT';links.new(geo.outputs['Incoming'],dot.inputs[0]);links.new(bump.outputs['Normal'],dot.inputs[1])
    cosine=op('ABSOLUTE',dot.outputs['Value']);grazing=op('SUBTRACT',1,cosine)
    fres=op('ADD',q['fresnel'][0],op('MULTIPLY',op('POWER',grazing,q['fresnelPower']),q['fresnel'][1]),'Reflection balance v40')
    mix=node('ShaderNodeMixShader','Live reflection and refraction v40');links.new(fres,mix.inputs[0]);links.new(refract.outputs[0],mix.inputs[1]);links.new(reflect.outputs[0],mix.inputs[2])
    optical=op('DIVIDE',q['hazeOpticalDepth'],op('MAXIMUM',cosine,.03))
    scatter=op('MULTIPLY',op('SUBTRACT',1,op('EXPONENT',op('MULTIPLY',optical,-1))),q['hazeStrength'],'Shallow water scattering amount v40')
    # Convert a single measured blue-green pigment to this scene's AgX space.
    pigment=node('ShaderNodeGroup','Water body display pigment v40');pigment.node_tree=bpy.data.node_groups['Poster source color to native AgX v38']
    c=[v/255 for v in q['hazeColorDisplay']];pigment.inputs[0].default_value=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    if 'hazeColorDisplayNear' in q:
        near=node('ShaderNodeRGB','Near water body pigment v40');c=[v/255 for v in q['hazeColorDisplayNear']];near.outputs[0].default_value=(*[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c],1)
        distance=node('ShaderNodeMapRange','Water body view-angle color v40');distance.inputs['From Min'].default_value=q['hazeCosineRange'][0];distance.inputs['From Max'].default_value=q['hazeCosineRange'][1];distance.clamp=True;links.new(cosine,distance.inputs['Value'])
        color_mix=node('ShaderNodeMixRGB','Far to near water pigments v40');color_mix.inputs[1].default_value=(*pigment.inputs[0].default_value,1);links.new(near.outputs[0],color_mix.inputs[2]);links.new(distance.outputs[0],color_mix.inputs[0]);links.new(color_mix.outputs[0],pigment.inputs[0])
    em=node('ShaderNodeEmission','Approximate shallow body scattering v40');em.inputs['Strength'].default_value=1;links.new(pigment.outputs[0],em.inputs['Color'])
    path=node('ShaderNodeLightPath','Water ray types v40')
    visible=op('MAXIMUM',path.outputs['Is Camera Ray'],path.outputs['Is Glossy Ray'])
    scatter=op('MULTIPLY',scatter,visible)
    haze=node('ShaderNodeMixShader','Soften submerged contrast v40');links.new(scatter,haze.inputs[0]);links.new(mix.outputs[0],haze.inputs[1]);links.new(em.outputs[0],haze.inputs[2])
    visible_surface=haze.outputs[0]
    if q.get('glintStrength',0):
        # Sparse crest streaks belong to world-space water, so they remain
        # attached to the surface under orbiting and animate with the waves.
        mask_pos=node('ShaderNodeCombineXYZ','Glint patch coordinates v40')
        for i,(axis,scale) in enumerate([('X',q.get('glintPatchScale',[.10,.65])[0]),('Y',q.get('glintPatchScale',[.10,.65])[1]),('Z',0)]):links.new(op('MULTIPLY',xyz.outputs[axis],scale),mask_pos.inputs[i])
        patch=node('ShaderNodeTexNoise','Broken glint patches v40');patch.inputs['Scale'].default_value=1;patch.inputs['Detail'].default_value=2;links.new(mask_pos.outputs[0],patch.inputs['Vector'])
        ramp=node('ShaderNodeMapRange','Sparse glint coverage v40');ramp.inputs['From Min'].default_value=q.get('glintCoverage',[.47,.62])[0];ramp.inputs['From Max'].default_value=q.get('glintCoverage',[.47,.62])[1];ramp.clamp=True;links.new(patch.outputs['Fac'],ramp.inputs['Value'])
        phase=op('ADD',op('MULTIPLY',xyz.outputs['Y'],-q.get('glintFrequency',11.5)),op('MULTIPLY',op('SINE',op('MULTIPLY',xyz.outputs['X'],.15)),.28))
        phase=op('ADD',phase,op('MULTIPLY',op('SUBTRACT',noise.outputs['Fac'],.5),q.get('glintWarp',0)))
        phase=op('ADD',phase,op('MULTIPLY',time.outputs[0],.22))
        crest=op('POWER',op('MAXIMUM',op('SINE',phase),0),58)
        amount=op('MULTIPLY',op('MULTIPLY',op('MULTIPLY',crest,ramp.outputs[0]),q['glintStrength']),visible)
        color=node('ShaderNodeGroup','Glint display pigment v40');color.node_tree=pigment.node_tree
        color.inputs[0].default_value=[((v/255+.055)/1.055)**2.4 for v in q['glintColorDisplay']]
        light=node('ShaderNodeEmission','Painted crest highlights v40');light.inputs['Strength'].default_value=1;links.new(color.outputs[0],light.inputs['Color'])
        streak=node('ShaderNodeMixShader','Sparse crest highlights v40');links.new(amount,streak.inputs[0]);links.new(visible_surface,streak.inputs[1]);links.new(light.outputs[0],streak.inputs[2]);visible_surface=streak.outputs[0]
    shadow=node('ShaderNodeBsdfTransparent','Shallow water shadow transmission v40');shadow.inputs['Color'].default_value=(*q['shadowTransmission'],1)
    final=node('ShaderNodeMixShader','Sunlight through shallow water v40');links.new(path.outputs['Is Shadow Ray'],final.inputs[0]);links.new(visible_surface,final.inputs[1]);links.new(shadow.outputs[0],final.inputs[2])
    out=node('ShaderNodeOutputMaterial','Poster water surface v40');links.new(final.outputs[0],out.inputs['Surface'])
    for i,n in enumerate(nodes):n.location=((i%9)*220,-(i//9)*240)
    mat['water_revision']='v40';mat['poster_water_parameters']=json.dumps(q);mat['world_space_waves']=True;mat['source_image_in_water_shader']=False
    return mat
