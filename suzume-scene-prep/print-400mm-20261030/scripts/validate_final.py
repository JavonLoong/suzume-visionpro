import json,hashlib,warnings,zipfile
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];O=R/'交付文件';warnings.filterwarnings('ignore')
d=json.loads((O/'零件清单.json').read_text(encoding='utf8'));reports=[]
for row in d['parts']:
 p=O/'STL_毫米'/(row['id']+'.stl');m=trimesh.load(p,force='mesh',process=True)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0,row['id']
 assert np.allclose(m.extents,row['size_mm'],atol=.001),(row['id'],m.extents,row['size_mm'])
 assert max(m.extents[:2])<225 and m.extents[2]<245
 assert abs(m.bounds[0,2])<.001
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['stl_sha256']
 if row['id'].startswith('B'):assert m.volume>150000 and min(m.extents[:2])>199
 with zipfile.ZipFile(O/'拓竹X1C工程_逐件'/(row['id']+'.3mf')) as z:
  c=json.loads(z.read('Metadata/project_settings.config'))
  assert c['printer_settings_id']=='Bambu Lab X1 Carbon 0.4 nozzle'
  assert len(c['inherits_group'])==len(c['filament_settings_id'])+2
 reports.append({'part':row['id'],'watertight':True,'winding_consistent':True,'bed_fit':True,'units':'millimeter','volume_mm3':round(m.volume,3),'sha256':row['stl_sha256']})
 print('VALIDATED',row['id'],flush=True)
assert len(list((O/'STL_毫米').glob('*.stl')))==len(d['parts'])
assert len(list((O/'拓竹X1C工程_逐件').glob('*.3mf')))==len(d['parts'])
d['export_validation']=reports
(O/'零件清单.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
(R/'analysis/final-validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('ALL_VALIDATED',len(reports),flush=True)
