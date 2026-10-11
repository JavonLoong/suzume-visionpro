"""Film shore contours lifted to real sloped slabs and a complete courtyard bank."""
from pathlib import Path
import json, math, numpy as np
from projection_geometry_v24 import P,center
R=Path(__file__).parent;O=R/'movie-shore-v26';O.mkdir(exist_ok=True)
C=np.array([P['cameraX'],-P['distance'],P['cameraZ']]);f=1656*P['lensMm']/36;c,s=math.cos(P['pitch']),math.sin(P['pitch'])
def ray(u,v):
    b=(828-v)/f
    return np.array([(u-1276)/f,c+b*s,b*c-s])
def on_height(u,v,z):
    d=ray(u,v);t=(z-C[2])/d[2];assert t>0
    return (C+t*d).tolist()
def on_ring(u,v,r=22.35):
    d=ray(u,v);o=C-center;roots=np.roots([d[:2]@d[:2],2*o[:2]@d[:2],o[:2]@o[:2]-r*r])
    return (C+max(roots)*d).tolist()
def project(p):
    x,y,z=np.array(p)-C;depth=y*c-z*s
    return [1276+f*x/depth,828-f*(y*s+z*c)/depth]
# Each contour contains a height estimate in scene units. They are not
# coplanar image cards: the top is triangulated in XY and closes at the bed.
contours=[
 ('left sunken rim',[[0,918,.09],[62,909,.10],[123,912,.08],[204,910,.10],[255,923,.06],[315,916,.09],[360,901,.10],[433,902,.10],[575,900,.09],[590,910,.08],[604,922,.06],[336,935,.045],[160,938,.035],[0,944,.04]]),
 ('left collapsed bank',[[0,842,.32],[49,830,.45],[99,842,.38],[157,866,.15],[233,863,.16],[266,872,.06],[322,854,.28],[405,842,.36],[470,842,.36],[540,853,.27],[606,845,.41],[642,827,.53],[685,829,.53],[757,873,.12],[815,880,.08],[875,873,.12],[907,846,.35],[925,823,.42],[910,810,.43],[720,808,.43],[540,806,.44],[330,804,.46],[140,803,.48],[0,800,.51]]),
 ('right collapsed bank',[[1525,818,.43],[1660,810,.43],[1810,816,.44],[1970,820,.44],[2130,828,.44],[2300,831,.44],[2460,827,.43],[2460,848,.38],[2419,859,.32],[2421,882,.20],[2387,901,.13],[2380,927,.08],[2341,932,.06],[2240,934,.05],[2110,926,.06],[1990,919,.07],[1892,919,.075],[1869,907,.09],[1750,904,.12],[1739,888,.18],[1650,891,.17],[1580,877,.24],[1525,879,.22]]),
 ('right slanted ridge',[[1550,842,.33],[1600,829,.47],[1666,824,.51],[1760,847,.37],[1902,863,.25],[2115,858,.33],[2240,853,.41],[2310,867,.30],[2300,890,.16],[2100,881,.23],[1870,886,.17],[1750,866,.29],[1630,863,.31],[1560,855,.31]])
]
slabs=[]
for name,pts in contours:
    native=[on_height(*p) for p in pts]
    slabs.append({'name':name,'referenceVertices':pts,'pointsNative':native,'projected':[project(p) for p in native],'bottom':-.22})
paths=[
 ('left upper return',[[1270,716],[1000,716],[700,714],[440,712],[250,710],[208,710],[183,718],[173,737],[172,774],[172,810]],.135),
 ('right upper return',[[1720,809],[1719,773],[1719,745],[1730,723],[1754,713],[1820,712],[2030,714],[2240,716],[2398,718],[2430,726],[2448,744],[2451,782],[2455,820]],.135),
 ('left lower main',[[0,778],[230,776],[470,773],[730,772],[1000,773],[1270,775]],.245),
 ('right broken lower main',[[1380,777],[1620,778],[1850,780],[2080,782],[2252,793]],.245)
]
pipes=[]
for name,pixels,r in paths:
    pts=[on_ring(*p) for p in pixels]
    pipes.append({'name':name,'pointsNative':pts,'referenceCenters':pixels,'radius':r,'wall':.024 if r>.2 else .017})
spec={'revision':26,'reference':'reference-opening-50525.jpg','referenceDimensions':[2552,1656],
      'centerNative':center.tolist(),'slabs':slabs,'observedPipes':pipes,
      'bank':{'outerRadius':23.25,'innerRadius':20.75,'height':.36,'bottom':-.22,'curbRadius':21.35,'curbWidth':.20,'curbTop':.57},
      'pipeRadius':22.35,'oneToOneComplete':False,
      'assumptions':['Slab heights, pipe radius and concealed depths are inferred from the reference and the v24 camera.','Observed visible contours are lifted onto sloped thick solids; they remain physical geometry from other viewpoints.','Bank and pipework outside the visible movie arc are inferred, with the south entrance left open.']}
(O/'shore-fit-v26.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'slabs':len(slabs),'pipes':len(pipes),'heightRanges':{p['name']:[min(q[2] for q in p['pointsNative']),max(q[2] for q in p['pointsNative'])] for p in pipes}},indent=2))
