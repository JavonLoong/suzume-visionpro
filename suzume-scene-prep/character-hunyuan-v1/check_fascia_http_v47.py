from pathlib import Path
import json,hashlib,requests
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-fascia-v47';base='http://127.0.0.1:8931/'
previous=json.loads((R/'poster-railings-v46/browser-http-verification-v46.json').read_text());files=[q['path'] for q in previous['resources'] if q['path']!='viewer/poster-v46.html'];files+=['viewer/poster-v47.html','poster-fascia-v47/browser-fascia-v47.json'];rows=[]
for name in dict.fromkeys(files):
    response=requests.get(base+quote(name,safe='/'),timeout=30);response.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(response.content).hexdigest()==sha;rows.append({'path':name,'bytes':len(response.content),'sha256':sha})
name='poster-fascia-v47/Suzume_dual_scene_fascia_v47.blend';response=requests.head(base+name,timeout=30);response.raise_for_status();assert int(response.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v47.json').write_text(json.dumps({'revision':47,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'browserAttempt':'Chrome unavailable; Edge listTabs failed with nodeRepl.fetch request failed in v47.','scope':'HTTP resource bytes only.'},indent=2));print('FASCIA_47_HTTP_VERIFIED',len(rows))
