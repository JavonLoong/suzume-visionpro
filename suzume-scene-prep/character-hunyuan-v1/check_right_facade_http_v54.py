from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-right-facade-v54';prior=json.loads((R/'poster-low-rails-v53/browser-http-verification-v53.json').read_text());files=[q['path'] for q in prior['resources'] if q['path']!='viewer/poster-v53.html'];files+=['viewer/poster-v54.html','poster-right-facade-v54/browser-right-facade-v54.json','poster-right-facade-v54/right-facade-v54.bin','poster-right-facade-v54/right-facade-pigments-v54.png'];rows=[]
for name in files:
 r=requests.get('http://127.0.0.1:8931/'+quote(name,safe='/'),timeout=30);r.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==sha;rows.append({'path':name,'sha256':sha,'bytes':len(r.content)})
name='poster-right-facade-v54/Suzume_dual_scene_right_facade_v54.blend';r=requests.head('http://127.0.0.1:8931/'+name,timeout=15);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v54.json').write_text(json.dumps({'revision':54,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP bytes only; no browser/GPU display verified.'},indent=2));print('RIGHT_FACADE_54_HTTP_VERIFIED',len(rows))
