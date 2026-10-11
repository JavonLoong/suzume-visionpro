from pathlib import Path
import requests,json,hashlib
from urllib.parse import quote
R=Path(__file__).parent;O=R/'poster-upper-windows-v48';prior=json.loads((R/'poster-fascia-v47/browser-http-verification-v47.json').read_text());files=[q['path'] for q in prior['resources'] if q['path']!='viewer/poster-v47.html'];files+=['viewer/poster-v48.html','poster-upper-windows-v48/browser-upper-windows-v48.json','poster-upper-windows-v48/upper-facade-v48.bin','poster-upper-windows-v48/upper-facade-pigments-v48.png'];rows=[]
files.append('poster-upper-windows-v48/clean-facade-pigments-v48.png')
for name in files:
 r=requests.get('http://127.0.0.1:8931/'+quote(name,safe='/'),timeout=30);r.raise_for_status();sha=hashlib.sha256((R/name).read_bytes()).hexdigest();assert hashlib.sha256(r.content).hexdigest()==sha;rows.append({'path':name,'sha256':sha,'bytes':len(r.content)})
name='poster-upper-windows-v48/Suzume_dual_scene_upper_windows_v48.blend';r=requests.head('http://127.0.0.1:8931/'+name,timeout=15);r.raise_for_status();assert int(r.headers['Content-Length'])==(R/name).stat().st_size
(O/'browser-http-verification-v48.json').write_text(json.dumps({'revision':48,'resources':rows,'nativeDownloadAvailable':True,'browserRuntimeVerified':False,'scope':'HTTP bytes; browser connection last failed in v47.'},indent=2));print('UPPER_WINDOWS_48_HTTP_VERIFIED',len(rows))
