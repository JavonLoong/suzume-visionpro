from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-horizon-v42';base='http://127.0.0.1:8931/'
files=['viewer/poster-v42.html','viewer/three.min.js','viewer/GLTFLoader.js','poster-horizon-v42/browser-clouds-v42.json','poster-horizon-v42/clouds-v42.bin','poster-steel-v39/browser-steel-v39.json','poster-steel-v39/steel-v39.bin','viewer/character-v37/suzume-posed-v37.gltf']
gltf=json.loads((R/files[-1]).read_text());files += ['viewer/character-v37/'+q['uri'] for key in ['buffers','images'] for q in gltf.get(key,[]) if 'uri' in q and not q['uri'].startswith('data:')]
rows=[]
for name in dict.fromkeys(files):
    r=requests.get(base+quote(name,safe='/'),timeout=30);r.raise_for_status();local=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==local,name;rows.append({'path':name,'bytes':len(r.content),'sha256':local})
name='poster-horizon-v42/Suzume_dual_scene_horizon_v42.blend';r=requests.head(base+name,timeout=30);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v42.json').write_text(json.dumps({'revision':42,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'Local HTTP resources and hashes only. Browser inventory succeeded, but opening the Edge candidate timed out after 20 seconds in v42.'},indent=2),encoding='utf-8');print('HORIZON_42_HTTP_VERIFIED',len(rows))
