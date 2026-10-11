from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-foreground-v51';L=R/'poster-lower-facade-v50';D=json.loads((O/'foreground-geometry-v51.json').read_text());v=json.loads((O/'verification-v51.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(O/'Suzume_dual_scene_foreground_v51.blend')==v['nativeSha256']
reference=Image.open(L/'reference-lower-facade-v50.png').convert('RGB');before=Image.open(L/'lower-facade-detail-v50.png').convert('RGB').crop((0,0,900,315));after=Image.open(O/'foreground-detail-v51.png').convert('RGB').crop((0,75,900,390));assert reference.size==before.size==after.size==(900,315)
canvas=Image.new('RGB',(900,1023),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(reference,'Reference'),(before,'Before v50'),(after,'After v51')]):draw.text((8,i*341+5),label,fill='white');canvas.paste(im,(0,i*341+26))
canvas.save(O/'foreground-comparison-v51.png')
# Compare the two supporting leg assemblies with their landing surface.
stone=next(q for q in D['members'] if q['name']=='Poster chair landing stone v51');top=float(np.array(stone['verticesNative'])[:,2].max());feet=[]
for q in D['members']:
 if q['name'].startswith('Poster chair leg frame'):
  z=float(np.array(q['verticesNative'])[:,2].min());penetration=top-z;assert 0<=penetration<.01;feet.append({'name':q['name'],'minimumZ':z,'supportTopZ':top,'contactOverlapMeters':penetration})
report={'revision':51,'nativeSha256':v['nativeSha256'],'chairLegSupportContacts':feet,'newLeaves':sum(q.get('leafCount',0) for q in D['members']),'newGrassBlades':sum(q.get('blades',0) for q in D['members']),'addedTriangles':sum(len(q['triangles']) for q in D['members']),'oldPropTrianglesRemoved':sum(q['removedTriangles'] for q in v['changedOriginalMeshes']),'selectedLargeLeavesRemoved':v['ivy']['removedCount'],'sourceComparisonCrop708':[0,600,300,705],'scope':'Chair support overlap and matched image crops. Hidden construction and vegetation depth remain inferred; these checks do not establish complete visual fidelity.','oneToOneComplete':False}
(O/'foreground-contact-audit-v51.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('FOREGROUND_51_COMPARED',report['newLeaves'],report['newGrassBlades'],feet)
