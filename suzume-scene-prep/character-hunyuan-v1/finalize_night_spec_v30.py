"""Choose the ragged bank trial and reduce its blue cast for the full-scene check."""
from pathlib import Path
import json,sys
R=Path(__file__).parent;O=R/'movie-night-v30';sys.path.insert(0,str(R/'color-pipeline-deps'));import PyOpenColorIO as ocio
q=json.loads((O/'night-shape-trials-v30.json').read_text())[0]
q.update(name='ragged-gray-violet-banks',density=.070,emissionGain=1.10,turbulence=1.15)
q['cloudDisplayColors']['main']=[78,74,78]
cfg=ocio.Config.CreateFromFile('C:/Program Files/Blender Foundation/Blender 5.0/5.0/datafiles/colormanagement/config.ocio');inverse=cfg.getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_INVERSE).getDefaultCPUProcessor()
q['cloudLinearColors']={k:[float(x/2**.8) for x in inverse.applyRGB([c/255 for c in rgb])] for k,rgb in q['cloudDisplayColors'].items()}
q['limitations']+=['Individual cloud silhouettes, the hard meadow horizon and distant low haze still differ from the film reference.','Night scene exposure is matched to the daytime portal view at 0.8 stops; browser tone and scattering equivalence remain unverified.']
(O/'night-spec-v30.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8');print('NIGHT_SPEC_FINALIZED')
