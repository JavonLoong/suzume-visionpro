from pathlib import Path
import json,numpy as np,urllib.request,hashlib
from scipy.spatial import cKDTree
R=Path(__file__).parent;O=R/'movie-door-v32';W=R/'viewer/character-v32';d=json.loads((W/'suzume-posed-v32.gltf').read_text());raw=[(W/b['uri']).read_bytes() for b in d['buffers']]
def values(index):
 a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];width={'VEC3':3,'SCALAR':1,'VEC2':2,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
 assert 'byteStride' not in v
 return np.frombuffer(raw[v['buffer']],dtype=dtype,count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
node=next(n for n in d['nodes'] if n['name'].startswith('Suzume Hunyuan textured surface'))
assert not any(k in node for k in ['matrix','translation','scale','rotation'])
p=values(d['meshes'][node['mesh']]['primitives'][0]['attributes']['POSITION']);native=np.c_[p[:,0],-p[:,2],p[:,1]]
target=np.load(O/'character-check-v32.npz')['after'];distance=cKDTree(target).query(native)[0];assert distance.max()<1e-6
reverse=cKDTree(native).query(target)[0];assert reverse.max()<1e-6
files=['viewer/candidate-v32.html']+['viewer/character-v32/'+x for x in ['suzume-posed-v32.gltf','suzume-posed-v32.glb']+[b['uri'] for b in d['buffers']]+[i['uri'] for i in d['images']]]
for f in files:
 with urllib.request.urlopen('http://127.0.0.1:8931/'+f,timeout=15) as response:
  assert response.status==200 and hashlib.sha256(response.read()).digest()==hashlib.sha256((R/f).read_bytes()).digest()
result={'revision':32,'exportedBodyVertices':len(p),'nativeBodyVertices':len(target),'maximumExportToNativeDistance':float(distance.max()),'maximumNativeToExportDistance':float(reverse.max()),'httpResourcesVerified':files,'packedGLBBytes':(W/'suzume-posed-v32.glb').stat().st_size,'browserRuntimeVerified':False}
(O/'character-asset-verification-v32.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
