"""Reuse the complete room/roof construction, replacing the measured windows."""
from pathlib import Path
import json,hashlib
R=Path(__file__).parent;O=R/'movie-bays-v23'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
source=(V/'round-hotel.js').read_text(encoding='utf-8')
body=source.split('    // Furniture and collapsed parasols remain solids when viewed from behind.')[0]
def replace(old,new):
    global body
    assert body.count(old)==1,(old,body.count(old))
    body=body.replace(old,new)
replace('for(let i=0;i<N;i++){','for(const spec of fit.bays){ const i=spec.index;')
replace("type=types[i]||'entrance-gap'","type=spec.openings.length?'movie-fit':(types[i]||'entrance-gap')")
replace("bay.name='Hotel bay '+i+' '+type;","bay.name='Hotel bay '+i+' '+type;bay.userData.bayIndex23=i;")
replace('curve(points,.012,moss,hotel);','const stem23=curve(points,.012,moss,hotel);stem23.userData.bayIndex23=i;stem23.name="Ivy stem";')
replace("if(type==='portico')holes.push", "if(type==='movie-fit')holes.push(...spec.openings.map(fittedOutline));\n        else if(type==='portico')holes.push")
replace('wallWithOpenings(w,raised?4.64:roofY-.20,holes,wmat,bay,.46);',"const lowerWall=wallWithOpenings(w,raised?4.64:roofY-.20,holes,wmat,bay,.46);lowerWall.name='Lower story wall';lowerWall.userData.geometryRole23='lowerWall';")
replace("if(type==='portico')portalEntrance(bay,i===17||i===23);", "if(type==='movie-fit')spec.openings.forEach(q=>fittedWindow(q,bay));\n        else if(type==='portico')portalEntrance(bay,i===17||i===23);")
helpers=r'''
function buildMovieBays23(T,scene,fit,resources){
  const {stoneMap,rustMap,paintMap,brass,moss}=resources,foliageSites=[];
  let seed23=230910;
  const rand=()=>{seed23=(Math.imul(seed23,1664525)+1013904223)>>>0;return seed23/4294967296;};
  const range=(a,b)=>a+(b-a)*rand();
  const material=(color,map=null,roughness=.85,metalness=0)=>new T.MeshStandardMaterial({color,map:map&&map.isTexture?map:null,roughness,metalness});
  const boxGeo=new T.BoxGeometry(1,1,1);
  function box(w,h,d,x,y,z,mat,parent=scene){const o=new T.Mesh(boxGeo,mat);o.scale.set(w,h,d);o.position.set(x,y,z);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
  function cylinder(a,b,h,x,y,z,mat,parent=scene){const o=new T.Mesh(new T.CylinderGeometry(a,b,h,16),mat);o.position.set(x,y,z);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
  function beam(a,b,width,depth,mat,parent=scene){const p=new T.Vector3(...a),q=new T.Vector3(...b),v=q.clone().sub(p);const o=box(width,v.length(),depth,0,0,0,mat,parent);o.position.copy(p.add(q).multiplyScalar(.5));o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),v.normalize());return o;}
  function curve(points,r,mat,parent=scene){const c=new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p)));const o=new T.Mesh(new T.TubeGeometry(c,Math.max(20,points.length*3),r,8,false),mat);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
  function fittedOutline(q){return q.type==='arch'?roundedOpening(q.x,q.bottom,q.width,q.height,q.rise):[[q.x-q.width/2,q.bottom],[q.x+q.width/2,q.bottom],[q.x+q.width/2,q.bottom+q.height],[q.x-q.width/2,q.bottom+q.height]];}
  function fittedWindow(q,parent){
    const g=new T.Group();g.name=q.name;parent.add(g);
    const shape=new T.Shape();fittedOutline(q).forEach((p,i)=>i?shape.lineTo(...p):shape.moveTo(...p));shape.closePath();
    const pane=new T.Mesh(new T.ShapeGeometry(shape),windowMat);pane.position.z=-.20;pane.name='Recessed '+q.name+' glazing';g.add(pane);
    const top=q.bottom+q.height,spring=q.type==='arch'?top-q.rise:top-.40,cols=q.panels*2;
    for(let j=0;j<=cols;j++)box(j%2===0?.046:.023,spring-q.bottom,.095,q.x-q.width/2+q.width*j/cols,(q.bottom+spring)/2,.026,mullionMat,g);
    for(let j=0;j<=4;j++)box(q.width,j===4?.065:.029,.095,q.x,q.bottom+(spring-q.bottom)*j/4,.032,mullionMat,g);
    if(q.type==='arch'){
      curve(roundedOpening(q.x,q.bottom,q.width,q.height,q.rise).map(p=>[...p,.04]),.038,mullionMat,g);
      for(let j=1;j<6;j++){const a=j*Math.PI/6;beam([q.x,spring,.04],[q.x+Math.cos(a)*q.width/2,spring+Math.sin(a)*q.rise,.04],.026,.045,mullionMat,g);}
      curve(roundedOpening(q.x,q.bottom,q.width+.09,q.height+.045,q.rise+.045).map(p=>[...p,.025]),.048,cornice,g);
    }else{
      for(let j=0;j<=cols;j++)box(.023,top-spring,.085,q.x-q.width/2+q.width*j/cols,(spring+top)/2,.025,mullionMat,g);
      box(q.width,.055,.11,q.x,top,.027,mullionMat,g);
      for(const side of [-1,1])box(.09,q.height+.1,.18,q.x+side*q.width/2,q.bottom+q.height/2,.015,cornice,g);
      box(q.width+.18,.095,.21,q.x,top+.02,.03,cornice,g);
      box(q.width+.23,.12,.42,q.x,top+.16,.12,cornice,g);
      box(q.width+.19,.038,.46,q.x,top+.23,.16,damp,g);
    }
    box(q.width+.18,.11,.26,q.x,q.bottom-.015,.06,cornice,g);
  }
'''
tail='\n    hotel.name="Movie rebuilt left and central bays v23";hotel.updateMatrixWorld(true);return hotel;\n}\n'
(O/'build_bays.js').write_text(helpers+body+tail,encoding='utf-8')
(O/'builder-provenance-v23.json').write_text(json.dumps({'source':'round-hotel.js','sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'changed':'Six measured ground-story windows in bays 12, 13 and 15. Complete room/upper-story/roof construction retained for bays 12–15, with procedural surface materials instead of poster pigments.','upperStoryIsNotMovieCalibrated':True},indent=2),encoding='utf-8')
print('BUILT_MOVIE_BAYS_23',len((helpers+body+tail).encode()))
