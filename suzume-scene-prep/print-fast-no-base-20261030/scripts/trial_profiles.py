from fast_common import *
from concurrent.futures import ThreadPoolExecutor
jobs=[]
for code in ['W02','S05']:
 src=min((OLD/'交付文件/拓竹X1C工程_逐件').glob(code+'*.3mf'),key=lambda p:len(p.name))
 for height in [.24,.28]:
  name=f'{code}_{int(height*100):02d}';inp=R/'trials'/(name+'.3mf');out=R/'trials'/(name+'.gcode.3mf')
  patch(src,inp,height);jobs.append((inp,out))
with ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(lambda args:slice_one(*args),jobs))
(R/'analysis/trial-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
