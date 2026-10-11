from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';base='http://127.0.0.1:8931/'
files=['viewer/poster-v43.html','viewer/three.min.js','viewer/GLTFLoader.js','poster-lower-clouds-v43/browser-clouds-v43.json','poster-lower-clouds-v43/lower-clouds-v43.bin','poster-horizon-v42/browser-clouds-v42.json','poster-horizon-v42/clouds-v42.bin','poster-steel-v39/browser-steel-v39.json','poster-steel-v39/steel-v39.bin','viewer/character-v37/suzume-posed-v37.gltf']
gltf=json.loads((R/files[-1]).read_text());files += ['viewer/character-v37/'+q['uri'] for key in ['buffers','images'] for q in gltf.get(key,[]) if 'uri' in q and not q['uri'].startswith('data:')]
rows=[]
for name in dict.fromkeys(files):
    response=requests.get(base+quote(name,safe='/'),timeout=30);response.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(response.content).hexdigest()==sha;rows.append({'path':name,'bytes':len(response.content),'sha256':sha})
name='poster-lower-clouds-v43/Suzume_dual_scene_lower_clouds_v43.blend';response=requests.head(base+name,timeout=30);response.raise_for_status();assert int(response.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v43.json').write_text(json.dumps({'revision':43,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP resource bytes only; browser opening and binding last timed out in v42.'},indent=2),encoding='utf-8');print('LOWER_CLOUD_43_HTTP_VERIFIED',len(rows))
