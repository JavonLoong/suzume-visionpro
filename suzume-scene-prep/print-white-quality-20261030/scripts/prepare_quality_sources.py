import json,warnings,numpy as np,trimesh
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R.parent/'print-400mm-20261030';P=R/'analysis/sources';P.mkdir(exist_ok=True)
warnings.filterwarnings('ignore');d=json.loads((OLD/'交付文件/零件清单.json').read_text(encoding='utf8'));parts={};notes=[];moves={}
for row in d['parts']:
 n=row['id']
 if n.startswith('B'):continue
 q=np.load(OLD/'analysis/assembly_meshes'/(n+'.npz'));m=trimesh.Trimesh(q['vertices'],q['faces'],process=True)
 if n.startswith('W') and '_附件' not in n:
  comps=sorted(m.split(only_watertight=False),key=lambda x:abs(x.volume),reverse=True);parts[n]=comps[0]
  for c in comps[1:]:
   if abs(c.volume)>1:
    target='S'+n[1:3]+'_钢架';moves.setdefault(target,[]).append(c)
    notes.append({'from':n,'to':target,'volume_mm3':abs(c.volume),'action':'将独立小景物并入其正下方的钢架安装底托'})
   else:notes.append({'from':n,'volume_mm3':abs(c.volume),'action':'删除小于1立方毫米的游离退化碎片'})
 else:parts[n]=m
for n,extras in moves.items():parts[n]=trimesh.util.concatenate([parts[n],*extras])
for n,m in parts.items():
 if n=='W08_环形建筑_附件34':m=m.convex_hull
 np.savez_compressed(P/(n+'.npz'),vertices=m.vertices,faces=m.faces)
(R/'analysis/adaptation-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf8')
(R/'analysis/source-manifest.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print('SOURCES_READY',len(parts),'TRANSFERS',sum(len(x) for x in moves.values()),flush=True)
