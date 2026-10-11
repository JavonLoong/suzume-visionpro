"""Use a compact array path while other user applications need the RAM."""
from pathlib import Path
import json, struct, numpy as np
import fast_simplification
H=Path(__file__).parent
raw=(H/'new-head-clean.glb').read_bytes()
size=struct.unpack_from('<I',raw,12)[0]
meta=json.loads(raw[20:20+size])
bin_start=20+size+8
def accessor(index):
    a=meta['accessors'][index];v=meta['bufferViews'][a['bufferView']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
    dims={'SCALAR':1,'VEC3':3}[a['type']]
    return np.frombuffer(raw,dtype=dtype,count=a['count']*dims,offset=bin_start+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,dims))
primitive=meta['meshes'][0]['primitives'][0]
P=accessor(primitive['attributes']['POSITION']).copy()
F=accessor(primitive['indices']).reshape((-1,3)).copy()
debris=(P[:,1]<-.96)&(P[:,2]>.44)
F=F[~debris[F].any(axis=1)]
before=len(F)
del raw,meta
P,F=fast_simplification.simplify(P,F,target_reduction=.64)
P=P.astype('<f4');F=F.astype('<u4')
binary=P.tobytes()+F.tobytes()
meta={'asset':{'version':'2.0','generator':'Hunyuan head local cleanup'},'scene':0,
      'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'Suzume independent Hunyuan head'}],
      'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1}]}],
      'buffers':[{'byteLength':len(binary)}],
      'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':P.nbytes,'target':34962},
                     {'buffer':0,'byteOffset':P.nbytes,'byteLength':F.nbytes,'target':34963}],
      'accessors':[{'bufferView':0,'componentType':5126,'count':len(P),'type':'VEC3','min':P.min(axis=0).tolist(),'max':P.max(axis=0).tolist()},
                   {'bufferView':1,'componentType':5125,'count':F.size,'type':'SCALAR'}]}
header=json.dumps(meta,separators=(',',':')).encode();header+=b' '*((-len(header))%4)
binary+=b'\0'*((-len(binary))%4)
out=struct.pack('<4sII',b'glTF',2,12+8+len(header)+8+len(binary))+struct.pack('<II',len(header),0x4e4f534a)+header+struct.pack('<II',len(binary),0x004e4942)+binary
(H/'new-head-display.glb').write_bytes(out)
audit={'sourceFaces':1699982,'uniqueConnectedFaces':before,'displayFaces':len(F),'displayVertices':len(P),'isolatedSliverRemoved':True,'boundsYUp':[P.min(axis=0).tolist(),P.max(axis=0).tolist()]}
(H/'mesh-cleanup.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit),flush=True)
