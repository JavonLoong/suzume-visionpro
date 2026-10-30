from fast_common import *
from concurrent.futures import ThreadPoolExecutor
plates=json.loads((R/'analysis/plates.json').read_text(encoding='utf8'))
def run(p):
 dst=R/'交付文件/复制到SD卡'/(p['code']+'.gcode.3mf')
 r=slice_one(Path(p['input']),dst)
 assert r['exit_code']==0 and r.get('gcode_files') and r.get('outside')=='false',r
 return r
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,plates))
(R/'analysis/final-slice-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('SLICED_ALL',len(results),'TOTAL_SECONDS',sum(r['seconds'] for r in results),'TOTAL_GRAMS',round(sum(r['grams'] for r in results),2),flush=True)
