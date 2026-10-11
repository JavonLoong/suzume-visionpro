"""World-space shallow-water controls shared by trials and the saved candidate."""
def apply_water(s,q):
    water=s.objects['Live planar reflective shallow water'];mat=water.data.materials[0];nodes=mat.node_tree.nodes
    reflect=nodes['Tinted water reflection'];reflect.inputs['Roughness'].default_value=q['reflectionRoughness'];reflect.inputs['Base Color'].default_value=(*q['reflectionTint'],1)
    refract=nodes['Shallow blue green transmission'];refract.inputs['Roughness'].default_value=q['transmissionRoughness'];refract.inputs['Color'].default_value=(*q['transmissionTint'],1);refract.inputs['IOR'].default_value=1.333
    fres=nodes['Artistic reflection balance'];fres.inputs[0].default_value=q['fresnel'][0]
    addition=fres.inputs[1].links[0].from_node;assert addition.operation=='MULTIPLY';addition.inputs[1].default_value=q['fresnel'][1]
    power=addition.inputs[0].links[0].from_node;assert power.operation=='POWER';power.inputs[1].default_value=q.get('fresnelPower',3)
    for i,base in enumerate([.0018,.00065,.00022],1):nodes['Wave height '+str(i)].inputs[1].default_value=base*q['rippleAmplitudeScale']
    mat['water_revision']='v29';mat['reflection_balance']=q['fresnel'];mat['wave_amplitudes_m']=[a*q['rippleAmplitudeScale'] for a in [.0018,.00065,.00022]]
    mat['movie_water_parameters']=__import__('json').dumps(q)
    if q.get('shadowTransmission'):
        links=mat.node_tree.links
        if not nodes.get('Shallow water shadow transmission v29'):
            path=nodes.new('ShaderNodeLightPath');path.name='Water ray types v29'
            trans=nodes.new('ShaderNodeBsdfTransparent');trans.name='Shallow water shadow transmission v29'
            mix=nodes.new('ShaderNodeMixShader');mix.name='Allow sunlight through shallow water v29'
            links.new(path.outputs['Is Shadow Ray'],mix.inputs[0]);links.new(nodes['Reflection and transmission'].outputs[0],mix.inputs[1]);links.new(trans.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes['Water surface'].inputs['Surface'])
        nodes['Shallow water shadow transmission v29'].inputs['Color'].default_value=(*q['shadowTransmission'],1)
    if 'algaeStrength' in q:apply_bed_algae(s,q)
    if q.get('hazeStrength'):
        links=mat.node_tree.links
        if not nodes.get('Shallow water scatter blend v29'):
            original=nodes['Water surface'].inputs['Surface'].links[0].from_socket
            def op(kind,a,b=None,name=None):
                n=nodes.new('ShaderNodeMath');n.operation=kind
                if name:n.name=name
                for v,i in [(a,0),(b,1)]:
                    if v is None:continue
                    if isinstance(v,(float,int)):n.inputs[i].default_value=v
                    else:links.new(v,n.inputs[i])
                return n.outputs[0]
            cosine=op('MAXIMUM',nodes['ABSOLUTE'].outputs[0],.03)
            depth=op('DIVIDE',q['hazeOpticalDepth'],cosine,'Water optical depth v29')
            attenuation=op('SUBTRACT',1,op('EXPONENT',op('MULTIPLY',depth,-1)))
            amount=op('MULTIPLY',attenuation,q['hazeStrength'],'Water scatter strength v29')
            path=nodes.get('Water ray types v29') or nodes.new('ShaderNodeLightPath');path.name='Water ray types v29'
            visible=op('MAXIMUM',path.outputs['Is Camera Ray'],path.outputs['Is Glossy Ray']);amount=op('MULTIPLY',amount,visible)
            em=nodes.new('ShaderNodeEmission');em.name='Blue shallow water scattering v29';em.inputs['Strength'].default_value=1
            mix=nodes.new('ShaderNodeMixShader');mix.name='Shallow water scatter blend v29';links.new(amount,mix.inputs[0]);links.new(original,mix.inputs[1]);links.new(em.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes['Water surface'].inputs['Surface'])
        nodes['Water optical depth v29'].inputs[0].default_value=q['hazeOpticalDepth'];nodes['Water scatter strength v29'].inputs[1].default_value=q['hazeStrength'];nodes['Blue shallow water scattering v29'].inputs['Color'].default_value=(*q['hazeColorLinear'],1)
    return mat

def apply_bed_algae(s,q):
    """Organic coloration on submerged stone tops, retaining physical paving."""
    touched=set()
    for ob in s.objects:
        if ob.type!='MESH' or not ob.name.startswith(('Flooded polygon flagstones and broken slabs solid mesh','Movie courtyard continuous basin bed')):continue
        for mat in ob.data.materials:
            if mat.name in touched:continue
            touched.add(mat.name);nodes=mat.node_tree.nodes;links=mat.node_tree.links
            if nodes.get('Bed algae amount v29'):
                nodes['Bed algae amount v29'].inputs[1].default_value=q['algaeStrength'];continue
            bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');base=bs.inputs['Base Color'];original=base.links[0].from_socket if base.is_linked else tuple(base.default_value)
            def op(kind,a,b=None,name=None):
                n=nodes.new('ShaderNodeMath');n.operation=kind
                if name:n.name=name
                for v,i in [(a,0),(b,1)]:
                    if v is None:continue
                    if isinstance(v,(int,float)):n.inputs[i].default_value=v
                    else:links.new(v,n.inputs[i])
                return n.outputs[0]
            geo=nodes.new('ShaderNodeNewGeometry');geo.name='Submerged stone world position v29'
            pos=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],pos.inputs[0]);normal=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],normal.inputs[0])
            noise=nodes.new('ShaderNodeTexNoise');noise.name='Broad organic algae patches v29';noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=.48;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.7;links.new(geo.outputs['Position'],noise.inputs['Vector'])
            ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Algae patch boundaries v29';ramp.color_ramp.elements[0].position=.44;ramp.color_ramp.elements[1].position=.67;links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
            fine=nodes.new('ShaderNodeTexNoise');fine.name='Fine algae speckles v29';fine.inputs['Scale'].default_value=9;fine.inputs['Detail'].default_value=2;links.new(geo.outputs['Position'],fine.inputs['Vector'])
            amount=op('MULTIPLY',op('MULTIPLY',ramp.outputs['Color'],fine.outputs['Fac']),q['algaeStrength'],'Bed algae amount v29')
            amount=op('MULTIPLY',amount,op('LESS_THAN',pos.outputs['Z'],.035));amount=op('MULTIPLY',amount,op('GREATER_THAN',normal.outputs['Z'],.6))
            mix=nodes.new('ShaderNodeMixRGB');mix.name='Submerged stone and algae v29';mix.blend_type='MIX';links.new(amount,mix.inputs[0]);mix.inputs[2].default_value=(.025,.15,.06,1)
            if isinstance(original,tuple):mix.inputs[1].default_value=original
            else:links.new(original,mix.inputs[1])
            links.new(mix.outputs[0],base);mat['submerged_algae_revision']=29
