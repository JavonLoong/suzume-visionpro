from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-right-bow-v56';prior=json.loads((R/'poster-right-arches-v55/browser-http-verification-v55.json').read_text());files=[q['path'] for q in prior['resources'] if q['path']!='viewer/poster-v55.html'];files+=['viewer/poster-v56.html','poster-right-bow-v56/browser-right-bow-v56.json','poster-right-bow-v56/right-bow-v56.bin','poster-right-bow-v56/right-bow-paint-v56.png'];rows=[]
files+=['poster-right-bow-v56/right-facade-beam-mask-v56.png','poster-right-bow-v56/right-arcade-beam-mask-v56.png']
for name in files:
 r=requests.get('http://127.0.0.1:8931/'+quote(name,safe='/'),timeout=30);r.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==sha;rows.append({'path':name,'sha256':sha,'bytes':len(r.content)})
name='poster-right-bow-v56/Suzume_dual_scene_right_bow_v56.blend';r=requests.head('http://127.0.0.1:8931/'+name,timeout=15);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v56.json').write_text(json.dumps({'revision':56,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP bytes only; no browser/GPU display verified.'},indent=2));print('RIGHT_BOW_56_HTTP_VERIFIED',len(rows))
