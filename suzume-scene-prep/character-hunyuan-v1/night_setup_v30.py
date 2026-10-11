"""Analytic spatial cloud banks and a night-sky color field, without image cards."""
import bpy,math,json
from mathutils import Matrix,Vector

class Nodes:
    def __init__(self,tree):self.nodes=tree.nodes;self.links=tree.links
    def feed(self,val,socket):
        if isinstance(val,(int,float)):socket.default_value=val
        else:self.links.new(val,socket)
    def op(self,kind,a,b=None,name=None):
        n=self.nodes.new('ShaderNodeMath');n.operation=kind
        if name:n.name=name
        self.feed(a,n.inputs[0])
        if b is not None:self.feed(b,n.inputs[1])
        return n.outputs[0]
    def xyz(self,x,y,z):
        n=self.nodes.new('ShaderNodeCombineXYZ')
        for val,socket in zip([x,y,z],n.inputs):self.feed(val,socket)
        return n.outputs[0]
    def smooth(self,a,b,x):
        t=self.op('MINIMUM',self.op('MAXIMUM',self.op('DIVIDE',self.op('SUBTRACT',x,a),b-a),0),1)
        return self.op('MULTIPLY',self.op('MULTIPLY',t,t),self.op('SUBTRACT',3,self.op('MULTIPLY',t,2)))
    def mix(self,a,b,t):
        n=self.nodes.new('ShaderNodeMixRGB');n.blend_type='MIX';n.use_clamp=False;self.feed(t,n.inputs[0]);self.links.new(a,n.inputs[1]);self.links.new(b,n.inputs[2]);return n.outputs[0]

def setup_sky(ob,q):
    m=ob.data.materials[0];tree=m.node_tree;tree.nodes.clear();n=Nodes(tree);op=n.op
    tc=n.nodes.new('ShaderNodeTexCoord');sub=n.nodes.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=(.5,.5,.5);n.links.new(tc.outputs['Generated'],sub.inputs[0])
    normalize=n.nodes.new('ShaderNodeVectorMath');normalize.operation='NORMALIZE';n.links.new(sub.outputs[0],normalize.inputs[0]);split=n.nodes.new('ShaderNodeSeparateXYZ');n.links.new(normalize.outputs[0],split.inputs[0])
    x=split.outputs['X'];height=op('MAXIMUM',split.outputs['Z'],0);east=n.smooth(-.11,.07,x)
    colors={k:n.xyz(*v) for k,v in q['skyLinearColors'].items()}
    horizon=n.mix(colors['leftHorizon'],colors['rightHorizon'],east);low=n.mix(colors['leftLow'],colors['rightLow'],east)
    color=n.mix(horizon,low,n.smooth(.005,.085,height));color=n.mix(color,colors['zenith'],n.smooth(.13,.8,height))
    em=n.nodes.new('ShaderNodeEmission');em.name='Film night sky radiance v30';em.inputs['Strength'].default_value=1;n.links.new(color,em.inputs['Color']);out=n.nodes.new('ShaderNodeOutputMaterial');n.links.new(em.outputs[0],out.inputs['Surface'])
    m['night_sky_revision']=30;m['display_exposure_calibration']=.8;m['reference_image_used']=False;m['sky_color_parameters']=json.dumps(q['skyDisplayColors'])

def setup_cloud(ob,row,q,index):
    # The original closed cube remains; its axes are now explicitly native XYZ.
    ob.parent=None;ob.matrix_world=Matrix.Translation(Vector(row['center']))@Matrix.Rotation(-row['tilt'],4,'Y')@Matrix.Diagonal((*row['halfSize'],1))
    m=ob.data.materials[0];tree=m.node_tree;tree.nodes.clear();n=Nodes(tree);op=n.op;seed=row['seed']
    tc=n.nodes.new('ShaderNodeTexCoord');split=n.nodes.new('ShaderNodeSeparateXYZ');n.links.new(tc.outputs['Generated'],split.inputs[0]);x,y,z=[op('SUBTRACT',op('MULTIPLY',split.outputs[k],2),1) for k in ['X','Y','Z']]
    shift=op('ADD',op('MULTIPLY',op('SINE',op('ADD',op('MULTIPLY',x,13),seed)),.24),op('MULTIPLY',op('SINE',op('ADD',op('ADD',op('MULTIPLY',x,43),op('MULTIPLY',y,.6)),seed*.8)),.10))
    h=op('SUBTRACT',z,shift)
    length=n.nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';n.links.new(n.xyz(op('MULTIPLY',x,.92),op('MULTIPLY',y,.9),op('MULTIPLY',h,1.25)),length.inputs[0]);envelope=op('SUBTRACT',1,length.outputs['Value'])
    # Correlated depth structure keeps ragged wisps visible after ray integration.
    a=op('SINE',op('ADD',op('MULTIPLY',x,45),op('SINE',op('ADD',op('MULTIPLY',h,3),seed))))
    b=op('SINE',op('ADD',op('ADD',op('MULTIPLY',h,9),op('MULTIPLY',y,.4)),seed))
    c=op('SINE',op('ADD',op('ADD',op('ADD',op('MULTIPLY',x,110),op('MULTIPLY',h,15)),op('MULTIPLY',y,.7)),seed*3))
    d=op('SINE',op('SUBTRACT',op('MULTIPLY',h,21),op('MULTIPLY',y,.6)))
    turbulent=op('MULTIPLY',op('ADD',op('MULTIPLY',op('MULTIPLY',a,b),.28),op('MULTIPLY',op('MULTIPLY',c,d),.12)),q['turbulence'])
    edge=op('MAXIMUM',op('MAXIMUM',op('ABSOLUTE',x),op('ABSOLUTE',y)),op('ABSOLUTE',z));fade=op('SUBTRACT',1,n.smooth(.82,1,edge))
    density=op('MULTIPLY',op('MULTIPLY',n.smooth(.06,.42,op('ADD',envelope,turbulent)),fade),q['density'],'Film cloud density coefficient v30')
    volume=n.nodes.new('ShaderNodeVolumePrincipled');volume.name='Film spatial cloud density v30';rgb=q['cloudDisplayColors'][row['tone']];linear=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in rgb];volume.inputs['Color'].default_value=(*linear,1);volume.inputs['Anisotropy'].default_value=.2
    n.links.new(density,volume.inputs['Density']);n.links.new(n.xyz(*q['cloudLinearColors'][row['tone']]),volume.inputs['Emission Color']);n.links.new(op('MULTIPLY',density,q['emissionGain'],'Film cloud emission gain v30'),volume.inputs['Emission Strength']);out=n.nodes.new('ShaderNodeOutputMaterial');n.links.new(volume.outputs[0],out.inputs['Volume'])
    m['night_volume_revision']=30;m['reference_image_used']=False;ob['movie_cloud_revision']=30;ob['movie_cloud_spec']=json.dumps(row);m['density_field']='finite three-dimensional ellipsoid with analytic multiscale wind perturbation and edge fade'

def apply_night(s,q):
    sky=bpy.data.objects['Native enclosing night sky'];setup_sky(sky,q)
    for i,row in enumerate(q['clouds']):setup_cloud(bpy.data.objects['Spatial twilight cloud volume '+str(i)],row,q,i)
    bpy.data.scenes['Night meadow through the door'].view_settings.exposure=.8
    bpy.context.view_layer.update()
