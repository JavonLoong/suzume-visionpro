from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-clouds-v41';base='http://127.0.0.1:8931/'
files=['viewer/poster-v41.html','viewer/three.min.js','viewer/GLTFLoader.js','poster-clouds-v41/browser-clouds-v41.json','poster-clouds-v41/clouds-v41.bin','poster-steel-v39/browser-steel-v39.json','poster-steel-v39/steel-v39.bin','viewer/character-v37/suzume-posed-v37.gltf']
gltf=json.loads((R/files[-1]).read_text());files += ['viewer/character-v37/'+q['uri'] for key in ['buffers','images'] for q in gltf.get(key,[]) if 'uri' in q and not q['uri'].startswith('data:')]
rows=[]
for name in dict.fromkeys(files):
    r=requests.get(base+quote(name,safe='/'),timeout=30);r.raise_for_status();local=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==local,name;rows.append({'path':name,'bytes':len(r.content),'sha256':local})
name='poster-clouds-v41/Suzume_dual_scene_clouds_v41.blend';r=requests.head(base+name,timeout=30);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v41.json').write_text(json.dumps({'revision':41,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'Local HTTP resources and hashes only. Last browser-control inventory timed out in v40.'},indent=2),encoding='utf-8');print('CLOUD_41_HTTP_VERIFIED',len(rows))
