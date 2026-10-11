from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-right-arches-v55';prior=json.loads((R/'poster-right-facade-v54/browser-http-verification-v54.json').read_text());files=[q['path'] for q in prior['resources'] if q['path']!='viewer/poster-v54.html'];files+=['viewer/poster-v55.html','poster-right-arches-v55/browser-right-arches-v55.json','poster-right-arches-v55/right-arches-v55.bin','poster-right-arches-v55/right-arcade-pigments-v55.png'];rows=[]
for name in files:
 r=requests.get('http://127.0.0.1:8931/'+quote(name,safe='/'),timeout=30);r.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==sha;rows.append({'path':name,'sha256':sha,'bytes':len(r.content)})
name='poster-right-arches-v55/Suzume_dual_scene_right_arches_v55.blend';r=requests.head('http://127.0.0.1:8931/'+name,timeout=15);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v55.json').write_text(json.dumps({'revision':55,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP bytes only; no browser/GPU display verified.'},indent=2));print('RIGHT_ARCHES_55_HTTP_VERIFIED',len(rows))
