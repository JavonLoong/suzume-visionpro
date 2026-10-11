"""Choose spatially varying mist after comparing weak and uniform dense trials."""
from pathlib import Path
import json,sys
R=Path(__file__).parent;O=R/'movie-terrain-v31';q=json.loads((O/'terrain-spec-v31.json').read_text(encoding='utf-8'));sys.path.insert(0,str(R/'color-pipeline-deps'));import PyOpenColorIO as ocio
inv=ocio.Config.CreateFromFile('C:/Program Files/Blender Foundation/Blender 5.0/5.0/datafiles/colormanagement/config.ocio').getProcessor('Linear Rec.709','sRGB','AgX',ocio.TRANSFORM_DIR_INVERSE).getDefaultCPUProcessor()
q.update(fogDensity=.045,fogEmissionGain=1.2,fogLateralX=[-7,4],fogLateralGain=[.244,.956],fogLeftDisplay=[22,23,70],fogRightDisplay=[37,32,62])
for side in ['Left','Right']:q['fog'+side+'Linear']=[float(v/2**.8) for v in inv.applyRGB([v/255 for v in q['fog'+side+'Display']])]
q['mistTrialEvidence']={'referenceLeftMedian':[19,15,33],'referenceRightMedian':[26,22,43],'weakLeftMedian':[22,19,29],'weakRightMedian':[17,14,26],'uniformDenseLeftMedian':[31,29,47],'uniformDenseRightMedian':[28,26,44],'note':'Final lateral density and color variation is an inferred spatial light field. Full rendering must still be reviewed.'}
(O/'terrain-spec-v31.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8');print('MIST_SPATIAL_COLOR_SELECTED')
