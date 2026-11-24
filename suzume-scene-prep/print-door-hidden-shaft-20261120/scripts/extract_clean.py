from pathlib import Path
import json, sys, numpy as np
sys.path.insert(0,r"D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/print-door-detail-20261113/scripts")
SRC=Path(r'D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/print-door-detail-20261113/scripts/build_detail.py')
text=SRC.read_text('utf-8').split(' # Relieve the jamb only')[0]
text=text.replace('[(1.25,50),(1.5,60),(1.75,70)]','[(1.5,60)]')
text='\n'.join(line for line in text.splitlines() if not line.startswith(('deck=','court=')))
g={'__file__':str(SRC)};exec(compile(text,str(SRC),'exec'),g)
O=Path(__file__).resolve().parents[1];(O/'analysis').mkdir(exist_ok=True)
for name in ['frame','leaf']:
 m=g['tm'](g[name]);np.savez_compressed(O/'analysis'/('clean_'+name+'.npz'),vertices=m.vertices,faces=m.faces)
print(json.dumps({k:np.array(g[k]).tolist() for k in ['body_bounds','body_y0','body_y1','scale']},indent=2))
for name in ['frame','leaf']:print(name,g[name].bounding_box())
for n in ['frame_src']:
 for i,m in enumerate(g[n]):
  m=g['transform'](m);print(n,i,m.bounding_box())

(O/"analysis/clean_component_bounds.json").write_text(json.dumps([list(m.bounding_box()) for m in g["leaf_parts"]]),"utf-8")
