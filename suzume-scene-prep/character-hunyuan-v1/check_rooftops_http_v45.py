from pathlib import Path
import json,hashlib,requests
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-rooftops-v45';base='http://127.0.0.1:8931/'
previous=json.loads((R/'poster-left-steel-v44/browser-http-verification-v44.json').read_text());files=[q['path'] for q in previous['resources'] if q['path']!='viewer/poster-v44.html']
files+=['viewer/poster-v45.html','poster-rooftops-v45/browser-rooftops-v45.json','poster-rooftops-v45/rooftops-v45.bin'];rows=[]
for name in dict.fromkeys(files):
    response=requests.get(base+quote(name,safe='/'),timeout=30);response.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(response.content).hexdigest()==sha;rows.append({'path':name,'bytes':len(response.content),'sha256':sha})
name='poster-rooftops-v45/Suzume_dual_scene_rooftops_v45.blend';response=requests.head(base+name,timeout=30);response.raise_for_status();assert int(response.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v45.json').write_text(json.dumps({'revision':45,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP resource bytes only. Browser control last failed in v44.'},indent=2),encoding='utf-8');print('ROOF_45_HTTP_VERIFIED',len(rows))
