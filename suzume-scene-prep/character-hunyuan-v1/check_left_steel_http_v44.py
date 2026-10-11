from pathlib import Path
import json,hashlib,requests
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-left-steel-v44';base='http://127.0.0.1:8931/'
files=['viewer/poster-v44.html','viewer/three.min.js','viewer/GLTFLoader.js','poster-left-steel-v44/browser-steel-v44.json','poster-left-steel-v44/steel-v44.bin','poster-lower-clouds-v43/browser-clouds-v43.json','poster-lower-clouds-v43/lower-clouds-v43.bin','poster-horizon-v42/browser-clouds-v42.json','poster-horizon-v42/clouds-v42.bin','viewer/character-v37/suzume-posed-v37.gltf']
gltf=json.loads((R/files[-1]).read_text());files+=['viewer/character-v37/'+q['uri'] for key in ['buffers','images'] for q in gltf.get(key,[]) if 'uri' in q and not q['uri'].startswith('data:')];rows=[]
for name in dict.fromkeys(files):
    response=requests.get(base+quote(name,safe='/'),timeout=30);response.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(response.content).hexdigest()==sha;rows.append({'path':name,'bytes':len(response.content),'sha256':sha})
name='poster-left-steel-v44/Suzume_dual_scene_left_steel_v44.blend';response=requests.head(base+name,timeout=30);response.raise_for_status();assert int(response.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v44.json').write_text(json.dumps({'revision':44,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP resource bytes only. Browser opening and binding last timed out in v42.'},indent=2),encoding='utf-8');print('LEFT_STEEL_44_HTTP_VERIFIED',len(rows))
