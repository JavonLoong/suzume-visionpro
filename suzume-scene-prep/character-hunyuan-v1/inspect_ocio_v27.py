"""Diagnose native color conversion for future pigment calibration; no image editing."""
from pathlib import Path
import sys,json,hashlib,numpy as np
R=Path(__file__).parent;sys.path.insert(0,str(R/'color-pipeline-deps'));import PyOpenColorIO as ocio
O=R/'movie-lighting-v27';config=Path('C:/Program Files/Blender Foundation/Blender 5.0/5.0/datafiles/colormanagement/config.ocio')
cfg=ocio.Config.CreateFromFile(str(config));forward=cfg.getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_FORWARD).getDefaultCPUProcessor();inverse=cfg.getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_INVERSE).getDefaultCPUProcessor()
reference=json.loads((O/'appearance-comparison-v27.json').read_text())['referencePatches'];exposure=.8;rows=[]
for name,q in reference.items():
    target=np.array(q['medianSrgb255'])/255;linear=np.array(inverse.applyRGB(target.tolist()))/(2**exposure);back=np.array(forward.applyRGB((linear*2**exposure).tolist()));clipped=np.maximum(linear,0);clippedBack=np.array(forward.applyRGB((clipped*2**exposure).tolist()))
    rows.append({'patch':name,'targetSrgb255':q['medianSrgb255'],'inverseSceneLinear':linear.tolist(),'allChannelsNonnegative':bool((linear>=0).all()),'mathematicalRoundtripMaxError255':float(np.max(np.abs(back-target))*255),'nonnegativeClampedMaxError255':float(np.max(np.abs(clippedBack-target))*255)})
result={'library':'OpenColorIO '+ocio.GetVersion(),'dependencyLocation':'color-pipeline-deps','config':str(config),'configSha256':hashlib.sha256(config.read_bytes()).hexdigest(),'view':'AgX','display':'sRGB','sceneLinear':'Linear Rec.709','exposure':exposure,'scope':'Only selected RGB values. No scene, material or image was changed. This is preparatory color mathematics, not a validated scene appearance.','samples':rows}
(O/'color-transform-diagnosis-v27.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2))
