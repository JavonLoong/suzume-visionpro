"""Fit rolling ridge heights in 3D and export exact shared terrain data."""
from pathlib import Path
import json,sys,numpy as np
from scipy.optimize import least_squares
from PIL import Image
R=Path(__file__).parent;O=R/'movie-terrain-v31';sys.path.insert(0,str(R));from terrain_geometry_v31 import height_field,adjusted_ground,extension_mesh
P=json.loads((R/'movie-projection-v24/joint-fit-v24.json').read_text())['parameters'];C=np.array([P['cameraX'],-P['distance'],P['cameraZ']]);f=1656*P['lensMm']/36;c=np.cos(P['pitch']);s=np.sin(P['pitch'])
anchors=np.array([[975,623],[1010,622],[1050,618],[1090,617],[1290,604],[1330,598],[1380,595],[1420,596]],float)
cx=[];cz=[]
for px,py in anchors:
    right=(px-1276)/f;up=(828-py)/f;d=np.array([right,c+up*s,-s+up*c]);pt=C+(145-C[1])/d[1]*d;cx.append(pt[0]);cz.append(pt[2])
q={'revision':31,'slope':.024,'ridgeWidth':25,'crestX':[-55]+cx+[55],'crestZ':[cz[0]]+cz+[cz[-1]],'outerRadius':510,'angularSegments':512,'radialSegments':36,'unchangedNearRadius':85,'fullyAdjustedRadius':105,'manualSkylineAnchors':anchors.tolist(),'referenceCamera':P,'geometryBeyondVisibleFrame':'inferred','oneToOneComplete':False}
depths=np.linspace(76,505,1800)
def skyline(px,q):
    x=C[0]+(depths-C[1])*(px-1276)/(f*c)
    for _ in range(3):
        z=height_field(x,depths,q);forward=c*(depths-C[1])-s*(z-C[2]);x=C[0]+(px-1276)/f*forward
    py=828-f*(s*(depths-C[1])+c*(z-C[2]))/forward;i=int(np.argmin(py));return float(py[i]),[float(x[i]),float(depths[i]),float(z[i])]
def residual(values):
    q['crestZ']=[values[0]]+values.tolist()+[values[-1]]
    return np.array([skyline(px,q)[0]-py for px,py in anchors])
fit=least_squares(residual,np.array(cz),bounds=(-3,4),max_nfev=60,xtol=1e-9,ftol=1e-9,gtol=1e-9);residual(fit.x)
q['skylineFit']=[{'pixel':p.tolist(),'projectedY':skyline(p[0],q)[0],'limitingTerrainPoint':skyline(p[0],q)[1]} for p in anchors]
q['fitNote']='Numerical height-field projection of manually annotated visible skyline. Native triangulation, occlusion and rendered appearance still require inspection.'
cfgpath='C:/Program Files/Blender Foundation/Blender 5.0/5.0/datafiles/colormanagement/config.ocio';sys.path.insert(0,str(R/'color-pipeline-deps'));import PyOpenColorIO as ocio
inv=ocio.Config.CreateFromFile(cfgpath).getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_INVERSE).getDefaultCPUProcessor()
q['fogColorDisplay']=[39,37,60];q['fogColorLinear']=[float(v/2**.8) for v in inv.applyRGB([v/255 for v in q['fogColorDisplay']])]
q['fogDensity']=.011;q['fogEmissionGain']=1.15
q['fogVolumes']=[{'name':'near low violet mist','center':[0,72,.55],'halfSize':[125,30,1.1],'seed':2.3,'weight':1.0},{'name':'distant low violet mist','center':[0,146,.25],'halfSize':[160,48,1.5],'seed':7.4,'weight':.55}]
original=np.load(O/'original-ground-v31.npz')['world'];ground=adjusted_ground(original,q);v,faces=extension_mesh(q)
ground.astype('<f4').tofile(O/'ground-world-v31.bin');v.astype('<f4').tofile(O/'extension-vertices-v31.bin');faces.astype('<u4').tofile(O/'extension-indices-v31.bin')
q['geometryCounts']={'groundVertices':len(ground),'extensionVertices':len(v),'extensionTriangles':len(faces)}
(O/'terrain-spec-v31.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
print('SKYLINE_FIT',json.dumps(q['skylineFit']));print('GEOMETRY_COUNTS',q['geometryCounts'])
