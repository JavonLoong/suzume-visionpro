from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-ground-v52';prior=json.loads((R/'poster-foreground-v51/browser-http-verification-v51.json').read_text());files=[q['path'] for q in prior['resources'] if q['path']!='viewer/poster-v51.html'];files+=['viewer/poster-v52.html','poster-ground-v52/browser-ground-v52.json','poster-ground-v52/ground-v52.bin'];rows=[]
for name in files:
 r=requests.get('http://127.0.0.1:8931/'+quote(name,safe='/'),timeout=30);r.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==sha;rows.append({'path':name,'sha256':sha,'bytes':len(r.content)})
name='poster-ground-v52/Suzume_dual_scene_ground_v52.blend';r=requests.head('http://127.0.0.1:8931/'+name,timeout=15);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v52.json').write_text(json.dumps({'revision':52,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP bytes only; no browser/GPU display verified.'},indent=2));print('GROUND_52_HTTP_VERIFIED',len(rows))
