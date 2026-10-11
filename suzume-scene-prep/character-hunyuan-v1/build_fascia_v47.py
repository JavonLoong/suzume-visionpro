from pathlib import Path
import json,numpy as np,trimesh
from shapely.geometry import Polygon
from shapely.ops import triangulate

R=Path(__file__).parent;O=R/'poster-fascia-v47'
S=json.loads((O/'source-fascia-v47.json').read_text())
# Section coordinates are inward distance from the facade chord and height.
# The back of this solid overlaps the original ceiling slab. The projecting
# lower drip edge is separate from the original roof/railing support above.
profile=np.array([[.16,6.445],[.285,6.445],[.325,6.405],
                  [.325,6.230],[.370,6.215],[.392,6.190],
                  [.392,6.160],[.310,6.130],[.16,6.130]])
poly=Polygon(profile);assert poly.is_valid
cap=[]
for tri in triangulate(poly):
    if poly.covers(tri):
        coords=np.asarray(tri.exterior.coords)[:3]
        cap.append([int(np.argmin(np.linalg.norm(profile-p,axis=1))) for p in coords])
assert len(cap)==len(profile)-2
edges=(np.arange(33)-16.5)*np.pi/16
edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
members=[]
for i in range(12,16):
    a0,a1=edges[i:i+2];angle=(a0+a1)/2;half=(a1-a0)/2
    rad=np.array([np.sin(angle),np.cos(angle),0]);tangent=np.array([np.cos(angle),-np.sin(angle),0]);chord=23.5*np.cos(half)
    vv=[]
    for sign in [-1,1]:
        for d,z in profile:
            # Miter the ends to the bay boundary; 9 mm of overlap avoids gaps.
            x=sign*((chord-d)*np.tan(half)+.009)
            vv.append(rad*(chord-d)+tangent*x+[0,0,z])
    n=len(profile);ff=[];mat=[]
    for j in range(n):
        k=(j+1)%n;ff.extend([[j,k,j+n],[k,k+n,j+n]])
        mat.extend([1 if j in [3,4,5] else 0]*2)
    for tri in cap:ff.extend([tri,[v+n for v in tri]]);mat.extend([0,0])
    m=trimesh.Trimesh(vv,ff,process=False);m.fix_normals();assert m.is_watertight and m.volume>0
    members.append({'name':f'Poster molded roof fascia bay {i} v47','bay':i,'verticesNative':np.asarray(m.vertices).round(8).tolist(),'triangles':m.faces.tolist(),'materialIndices':mat,'profileMeters':profile.tolist(),'backOverlapWithOriginalSlabMeters':.08})
data={'revision':47,'sourceNativeSha256':S['sourceNativeSha256'],'scope':'Solid molded facing on the four observed left roof slab edges. Original load-bearing slab, roof and railing are retained. The section and hidden return are inferred from the visible ledge.','members':members,'materials':[{'name':'Poster blue gray fascia plaster v47','linearRGB':[.98,.55,.40],'roughness':.92,'metalness':0},{'name':'Poster fascia drip edge v47','linearRGB':[.99,.69,.54],'roughness':.9,'metalness':0}],'oneToOneComplete':False}
(O/'fascia-geometry-v47.json').write_text(json.dumps(data,separators=(',',':')))
print('FASCIA_47_GEOMETRY',len(members),'closed solids',sum(len(x['triangles']) for x in members),'triangles')
