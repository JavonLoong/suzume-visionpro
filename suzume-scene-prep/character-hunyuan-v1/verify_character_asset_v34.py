from pathlib import Path
import json,numpy as np,urllib.request,hashlib,subprocess
from scipy.spatial import cKDTree
R=Path(__file__).parent;O=R/'movie-head-v34';W=R/'viewer/character-v34';d=json.loads((W/'suzume-posed-v34.gltf').read_text());raw=[(W/b['uri']).read_bytes() for b in d['buffers']]
def positions(index):
 a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];assert a['type']=='VEC3' and a['componentType']==5126 and 'byteStride' not in v
 return np.frombuffer(raw[v['buffer']],dtype='<f4',count=a['count']*3,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3)
checks=[]
for name,file in [('Suzume mathematical head v34',O/'head-check-v34.npz'),('Suzume Hunyuan textured surface',R/'movie-door-v32/character-check-v32.npz')]:
 node=next(n for n in d['nodes'] if n['name'].startswith(name));assert not any(k in node for k in ['matrix','translation','scale','rotation']);primitives=d['meshes'][node['mesh']]['primitives'];p=np.concatenate([positions(p['attributes']['POSITION']) for p in primitives]);native=np.c_[p[:,0],-p[:,2],p[:,1]];target=np.load(file)['after'];forward=cKDTree(target).query(native)[0];reverse=cKDTree(native).query(target)[0];assert max(forward.max(),reverse.max())<1e-6
 checks.append({'part':name,'materialPrimitives':len(primitives),'triangles':sum(d['accessors'][p['indices']]['count']//3 for p in primitives),'exportedVertices':len(p),'nativeVertices':len(target),'maximumExportDistance':float(forward.max()),'maximumNativeDistance':float(reverse.max())})
assert checks[0]['materialPrimitives']==12
files=['viewer/candidate-v34.html']+['viewer/character-v34/'+x for x in ['suzume-posed-v34.gltf','suzume-posed-v34.glb']+[b['uri'] for b in d['buffers']]+[i['uri'] for i in d['images']]]
for f in files:
 with urllib.request.urlopen('http://127.0.0.1:8931/'+f,timeout=15) as response:assert response.status==200 and hashlib.sha256(response.read()).digest()==hashlib.sha256((R/f).read_bytes()).digest()
html=(R/'viewer/candidate-v34.html').read_text(encoding='utf-8');assert "load('character-v34/suzume-posed-v34.gltf'" in html and 'makeDoorLeafRigid32(T,nightHinge)' in html and 'renderNight31(reflectionCam)' in html
js="const fs=require('fs'),vm=require('vm');for(const m of fs.readFileSync(process.argv[1],'utf8').matchAll(/<script(?:\\s[^>]*)?>([\\s\\S]*?)<\\/script>/g))if(m[1].trim())new vm.Script(m[1]);console.log('INLINE_SYNTAX_OK');"
subprocess.run(['C:/Program Files/nodejs/node.exe','-e',js,str(R/'viewer/candidate-v34.html')],check=True)
result={'revision':34,'meshChecks':checks,'httpResourcesVerified':files,'inlineSyntaxVerified':True,'rigidDoorAndDepthAwareNightPathsRetained':True,'browserRuntimeVerified':False}
(O/'browser-verification-v34.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
