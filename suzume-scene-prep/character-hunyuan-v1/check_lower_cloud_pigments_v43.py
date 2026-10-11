from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';a=np.load(O/'lower-cloud-geometry-v43.npz');spec=json.loads((O/'lower-cloud-geometry-v43.json').read_text());rows=[]
for q in spec['clouds']:
    rgb=a[q['key']+'_rgb'];green=(rgb[:,1]-rgb[:,2])>.025
    # The rejected side view had G-B about .08 display RGB. No such green
    # cloud pigment is compatible with this blue-grey reference sky.
    assert not green.any(),(q['name'],int(green.sum()))
    rows.append({'name':q['name'],'vertices':len(rgb),'greenExcessOverBlueMax':float((rgb[:,1]-rgb[:,2]).max()),'meanDisplayRGB':rgb.mean(0).tolist(),'greenContaminationThreshold':.025})
(O/'pigment-audit-v43.json').write_text(json.dumps({'revision':43,'clouds':rows,'previousSideFailure':'Grey-green foreground pigment was extrapolated across unobserved cloud front surfaces.','repair':'Require sky chroma in both reference images; measured pigments fade out outside verified cloud samples, revealing inferred normal-dependent 3D illumination.','scope':'Vertex pigment audit; final front and oblique renders are still required.'},indent=2),encoding='utf-8');print(json.dumps(rows,indent=2))
