"""Sample reference colors and lift observed cloud centers into a spatial scene."""
from pathlib import Path
from PIL import Image
import json,sys,math,numpy as np
R=Path(__file__).parent;O=R/'movie-night-v30';sys.path.insert(0,str(R/'color-pipeline-deps'));import PyOpenColorIO as ocio
im=np.asarray(Image.open(R/'movie-surfaces-v28/reference-opening.jpg').convert('RGB'))
boxes={'skyLeft':[995,290,1080,345],'skyMiddle':[1150,285,1230,350],'skyRight':[1310,295,1400,360],'mainCloudLeft':[980,478,1080,515],'mainCloudRight':[1350,464,1420,502],'lowerBlueHaze':[980,570,1060,601]}
samples={k:np.median(im[y0:y1,x0:x1].reshape(-1,3),0).tolist() for k,(x0,y0,x1,y1) in boxes.items()}
cfg=ocio.Config.CreateFromFile('C:/Program Files/Blender Foundation/Blender 5.0/5.0/datafiles/colormanagement/config.ocio');inverse=cfg.getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_INVERSE).getDefaultCPUProcessor()
def linear(rgb):return [float(v/2**.8) for v in inverse.applyRGB([v/255 for v in rgb])]
P=json.loads((R/'movie-projection-v24/joint-fit-v24.json').read_text())['parameters'];C=np.array([P['cameraX'],-P['distance'],P['cameraZ']]);f=1656*P['lensMm']/36;c=math.cos(P['pitch']);sn=math.sin(P['pitch'])
def lift(pixel,depth):
    right=(pixel[0]-1276)/f;up=(828-pixel[1])/f;direction=np.array([right,c+up*sn,-sn+up*c]);return (C+(depth-C[1])/direction[1]*direction).tolist()
# Pixel centers anchor visible banks; their depth and unobserved width remain inferred.
records=[
 {'name':'main silver blue bank','pixel':[1170,496],'depth':290,'halfSize':[66,23,4.2],'tilt':.095,'tone':'main','seed':1.0},
 {'name':'right trailing wisp','pixel':[1440,474],'depth':315,'halfSize':[42,15,2.7],'tilt':.13,'tone':'main','seed':3.5},
 {'name':'upper faint wisps','pixel':[1260,402],'depth':330,'halfSize':[68,17,2.1],'tilt':.12,'tone':'dim','seed':6.0},
 {'name':'left purple veil','pixel':[975,424],'depth':310,'halfSize':[44,19,3.0],'tilt':.13,'tone':'purple','seed':8.5},
 {'name':'lower blue bank','pixel':[1210,551],'depth':250,'halfSize':[62,18,2.3],'tilt':.065,'tone':'dim','seed':11.0},
 {'name':'far left continuation','center':[-140,280,14],'halfSize':[90,26,5.5],'tilt':.08,'tone':'dim','seed':13.0},
 {'name':'far right continuation','center':[145,295,16],'halfSize':[95,27,5.0],'tilt':.10,'tone':'purple','seed':16.0},
 {'name':'upper night bank','center':[-65,335,30],'halfSize':[100,26,5.3],'tilt':.06,'tone':'dim','seed':19.0},
 {'name':'side night bank','center':[180,140,28],'halfSize':[85,25,6.0],'tilt':.05,'tone':'dim','seed':23.0},
 {'name':'back night bank','center':[-110,-180,38],'halfSize':[110,28,8.0],'tilt':-.06,'tone':'purple','seed':27.0}
]
for rec in records:
    if 'pixel' in rec:rec['center']=lift(rec['pixel'],rec['depth'])
colors={'main':[85,88,102],'dim':[32,44,73],'purple':[49,32,63]}
sky={'leftHorizon':[26,18,55],'rightHorizon':[18,25,57],'leftLow':[29,19,66],'rightLow':[27,27,74],'zenith':[5,10,32]}
q={'revision':30,'clouds':records,'cloudDisplayColors':colors,'cloudLinearColors':{k:linear(v) for k,v in colors.items()},'skyDisplayColors':sky,'skyLinearColors':{k:linear(v) for k,v in sky.items()},'density':.045,'emissionGain':1.35,'turbulence':1.0,'cameraParameters':P,'referencePatchBoxes':boxes,'referencePatchMedians':samples,'referenceImageUsedInSkyOrClouds':False,'oneToOneComplete':False,'limitations':['Cloud centers are lifted from a single reference camera onto inferred depth planes. Full cloud depth and hidden shapes are inferred.','Analytic three-dimensional density and emission approximate painted cloud appearance; they are not measured atmospheric data.']}
(O/'night-spec-initial-v30.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8');print('REFERENCE_COLORS',json.dumps(samples));print('LIFTED_CENTERS',json.dumps([{k:r[k] for k in ['name','center','halfSize']} for r in records[:5]]))
