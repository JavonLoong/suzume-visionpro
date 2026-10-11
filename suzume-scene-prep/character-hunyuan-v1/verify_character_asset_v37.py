from pathlib import Path
import json,numpy as np,urllib.request,hashlib,subprocess
from scipy.spatial import cKDTree
from PIL import Image
R=Path(__file__).parent;O=R/'movie-collar-v37';W=R/'viewer/character-v37';d=json.loads((W/'suzume-posed-v37.gltf').read_text());raw=[(W/b['uri']).read_bytes() for b in d['buffers']]
def values(index,n):
 a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC'+str(n) and 'byteStride' not in v
 return np.frombuffer(raw[v['buffer']],dtype='<f4',count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
checks=[];uv_target=np.load(O/'export-uv-check-v37.npz')
for name,file,key,uv_key in [('Suzume mathematical head v37',O/'head-check-v37.npz','after',None),('Suzume Hunyuan textured surface',O/'character-check-v37.npz','after','body'),('Suzume rolled collar edge v37',O/'character-check-v37.npz','hem','hem')]:
 node=next(n for n in d['nodes'] if n['name'].startswith(name));assert not any(k in node for k in ['matrix','translation','scale','rotation']);primitives=d['meshes'][node['mesh']]['primitives'];p=np.concatenate([values(p['attributes']['POSITION'],3) for p in primitives]);native=np.c_[p[:,0],-p[:,2],p[:,1]];target=np.load(file)[key];forward=cKDTree(target).query(native)[0];reverse=cKDTree(native).query(target)[0];assert max(forward.max(),reverse.max())<1e-6
 check={'part':name,'materialPrimitives':len(primitives),'triangles':sum(d['accessors'][p['indices']]['count']//3 for p in primitives),'exportedVertices':len(p),'nativeVertices':len(target),'maximumPositionError':float(max(forward.max(),reverse.max()))}
 if uv_key:
  textured=[p for p in primitives if 'TEXCOORD_0' in p['attributes']];tex=np.concatenate([values(p['attributes']['TEXCOORD_0'],2) for p in textured]);tex[:,1]=1-tex[:,1];pv=np.concatenate([values(p['attributes']['POSITION'],3) for p in textured]);joined=np.c_[pv[:,0],-pv[:,2],pv[:,1],tex];expected=np.c_[target,uv_target[uv_key]];required=expected[uv_target['bodyTexturedMask']] if uv_key=='body' else expected;uv_error=max(cKDTree(expected).query(joined)[0].max(),cKDTree(joined).query(required)[0].max());assert uv_error<1e-6;check['positionAndUVPairError']=float(uv_error)
 checks.append(check)
assert checks[0]['materialPrimitives']==12 and checks[1]['materialPrimitives']==2 and checks[2]['materialPrimitives']==1
files=['viewer/candidate-v37.html']+['viewer/character-v37/'+x for x in ['suzume-posed-v37.gltf','suzume-posed-v37.glb']+[b['uri'] for b in d['buffers']]+[i['uri'] for i in d['images']]]
for f in files:
 with urllib.request.urlopen('http://127.0.0.1:8931/'+f,timeout=15) as response:assert response.status==200 and hashlib.sha256(response.read()).digest()==hashlib.sha256((R/f).read_bytes()).digest()
node=next(n for n in d['nodes'] if n['name'].startswith('Suzume Hunyuan textured'));mat=d['materials'][d['meshes'][node['mesh']]['primitives'][0]['material']];index=d['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source'];new_image=W/d['images'][index]['uri'];old_image=Path(json.loads((O/'uv-repair-v37.json').read_text())['baseColorImage']);assert Image.open(new_image).tobytes()==Image.open(old_image).tobytes()
html=(R/'viewer/candidate-v37.html').read_text(encoding='utf-8');assert "load('character-v37/suzume-posed-v37.gltf'" in html and 'makeDoorLeafRigid32(T,nightHinge)' in html and 'renderNight31(reflectionCam)' in html
js="const fs=require('fs'),vm=require('vm');for(const m of fs.readFileSync(process.argv[1],'utf8').matchAll(/<script(?:\\s[^>]*)?>([\\s\\S]*?)<\\/script>/g))if(m[1].trim())new vm.Script(m[1]);console.log('INLINE_SYNTAX_OK');";subprocess.run(['C:/Program Files/nodejs/node.exe','-e',js,str(R/'viewer/candidate-v37.html')],check=True)
result={'revision':37,'meshChecks':checks,'httpResourcesVerified':files,'bodyBaseColorPixelsPreserved':True,'collarUVExportVerified':True,'inlineSyntaxVerified':True,'rigidDoorAndDepthAwareNightPathsRetained':True,'browserRuntimeVerified':False};(O/'browser-verification-v37.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
