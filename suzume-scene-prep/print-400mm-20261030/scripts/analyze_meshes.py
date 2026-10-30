import numpy as np,trimesh,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
report={}
for cat in ['wall','steel','ground','frame','leaf','pedestal']:
 d=np.load(R/'analysis'/(cat+'.npz'))
 m=trimesh.Trimesh(d['vertices']*400/58,d['faces'],process=True)
 parts=m.split(only_watertight=False)
 rows=[]
 for c in parts:
  rows.append({'faces':len(c.faces),'volume':round(float(c.volume),4),'watertight':bool(c.is_watertight),'bounds':c.bounds.round(3).tolist(),'dims':c.extents.round(3).tolist()})
 rows.sort(key=lambda r:r['faces'],reverse=True)
 report[cat]=rows
 print(cat,'components',len(rows),'watertight',sum(r['watertight'] for r in rows),'large',json.dumps(rows[:8]),flush=True)
(R/'analysis'/'mesh-components.json').write_text(json.dumps(report,indent=2))
