// Shared geometry builder: executed with THREE in Node and in the local viewer.
function buildMovieBay21(T,scene,materials,fit){
  const group=new T.Group();group.name='Movie bay 16 rectangular and circular windows v21';
  group.position.set(Math.sin(fit.angle)*fit.chordRadius,0,-Math.cos(fit.angle)*fit.chordRadius);group.rotation.y=-fit.angle;scene.add(group);
  const w=fit.bayWidth,d=4.52,roof=fit.roofY,rect=fit.rectangle,circ=fit.oculus;
  const box=(x,y,z,sx,sy,sz,mat,name)=>{const m=new T.Mesh(new T.BoxGeometry(sx,sy,sz),materials[mat]);m.position.set(x,y,z);m.name=name||mat;m.castShadow=m.receiveShadow=true;group.add(m);return m;};
  function line(points,r,mat,name){const c=new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p)));const m=new T.Mesh(new T.TubeGeometry(c,Math.max(20,points.length*3),r,8,false),materials[mat]);m.name=name;m.castShadow=m.receiveShadow=true;group.add(m);return m;}
  function beam(a,b,width,depth,mat,name){const p=new T.Vector3(...a),q=new T.Vector3(...b),delta=q.clone().sub(p);const m=box(...p.clone().add(q).multiplyScalar(.5).toArray(),width,delta.length(),depth,mat,name);m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.normalize());return m;}
  function ellipse(x,y,rx,ry){return Array.from({length:65},(_,i)=>[x+rx*Math.cos(i*Math.PI/32),y+ry*Math.sin(i*Math.PI/32)]);}
  const rectangle=[[-rect.width/2+rect.x,rect.bottom],[rect.width/2+rect.x,rect.bottom],[rect.width/2+rect.x,rect.bottom+rect.height],[-rect.width/2+rect.x,rect.bottom+rect.height]];
  const circle=ellipse(circ.x,circ.centerY,circ.radiusX,circ.radiusY);
  const wallShape=new T.Shape();wallShape.moveTo(-w/2,0);wallShape.lineTo(w/2,0);wallShape.lineTo(w/2,roof-.2);wallShape.lineTo(-w/2,roof-.2);wallShape.closePath();
  for(const outline of [rectangle,circle]){const hole=new T.Path();outline.forEach((v,i)=>i?hole.lineTo(...v):hole.moveTo(...v));hole.closePath();wallShape.holes.push(hole);}
  const wallGeo=new T.ExtrudeGeometry(wallShape,{depth:.46,bevelEnabled:false,curveSegments:16});wallGeo.translate(0,0,-.46);
  const uv=wallGeo.attributes.uv;for(let i=0;i<uv.count;i++)uv.setXY(i,uv.getX(i)*.22,uv.getY(i)*.22);
  const wall=new T.Mesh(wallGeo,materials.sunWall);wall.name='Solid plaster wall with two through-openings';wall.castShadow=wall.receiveShadow=true;group.add(wall);
  function pane(outline,name){const s=new T.Shape();outline.forEach((v,i)=>i?s.lineTo(...v):s.moveTo(...v));s.closePath();const m=new T.Mesh(new T.ShapeGeometry(s),materials.windowMat);m.position.z=-.20;m.name=name;group.add(m);return m;}
  pane(rectangle,'Recessed rectangular glazing');pane(circle,'Recessed oculus glazing');
  const top=rect.bottom+rect.height,transom=top-.42,cols=6;
  for(let i=0;i<=cols;i++)box(rect.x-rect.width/2+i*rect.width/cols,(rect.bottom+transom)/2,.025,i%2===0?.050:.026,transom-rect.bottom,.10,'mullionMat','Rectangular vertical mullion');
  for(let i=0;i<=4;i++)box(rect.x,rect.bottom+(transom-rect.bottom)*i/4,.03,rect.width,.042,.10,'mullionMat','Rectangular horizontal mullion');
  for(let i=0;i<=cols*2;i++)box(rect.x-rect.width/2+i*rect.width/(cols*2),(transom+top)/2,.025,.022,top-transom,.09,'mullionMat','Transom grid');
  for(const x of [rect.x-rect.width/2,rect.x+rect.width/2])box(x,rect.bottom+rect.height/2,.015,.11,rect.height+.10,.18,'cornice','Window stone jamb');
  for(const y of [rect.bottom,top])box(rect.x,y,.03,rect.width+.19,.105,.21,'cornice','Window stone sill or lintel');
  line(circle.map(p=>[...p,.025]),.052,'cornice','Oculus stone rim');
  line(ellipse(circ.x,circ.centerY,circ.radiusX*.34,circ.radiusY*.34).map(p=>[...p,.052]),.020,'mullionMat','Oculus inner circular frame');
  for(let i=0;i<8;i++){const a=i*Math.PI/4;beam([circ.x,circ.centerY,.055],[circ.x+Math.cos(a)*circ.radiusX,circ.centerY+Math.sin(a)*circ.radiusY,.055],.025,.045,'mullionMat','Oculus radial spoke');}
  // The rear walls, room divisions and slab follow the original circular bay.
  box(0,(roof+.8)/2,-d,w,roof-.8,.32,'roomMat','Rear room wall');
  const half=(fit.edges[1]-fit.edges[0])/2;
  for(const side of [-1,1]){const q=box(side*(w/2+2.3*Math.tan(half)-.05),(roof+.8)/2,-2.3,.22,roof-.9,4.6/Math.cos(half),'sunWall','Radial room side wall');q.rotation.y=-side*half;}
  function slab(front,back,topY,thickness,mat,name){const hw=r=>(fit.chordRadius-r)*Math.tan(half)+.012;const shape=new T.Shape();shape.moveTo(-hw(front),front);shape.lineTo(hw(front),front);shape.lineTo(hw(back),back);shape.lineTo(-hw(back),back);shape.closePath();const geo=new T.ExtrudeGeometry(shape,{depth:thickness,bevelEnabled:false});const m=new T.Mesh(geo,materials[mat]);m.name=name;m.rotation.x=Math.PI/2;m.position.y=topY;m.castShadow=m.receiveShadow=true;group.add(m);}
  slab(.26,-4.53,.73,.95,'damp','Grounded structural podium');slab(.50,-4.55,.865,.19,'cornice','Walkway cap');
  slab(.12,-4.595,roof+.08,.16,'cornice','Roof slab');box(0,roof+.11,.025,w,.085,.30,'cornice','Upper cornice');
  box(0,roof+.30,-4.50,w,.52,.27,'sunWall','Rear parapet');
  const awning=top+.16;box(rect.x,awning,.16,rect.width+.24,.14,.49,'cornice','Rectangular window awning');box(rect.x,awning+.075,.20,rect.width+.20,.045,.56,'damp','Awning weathered upper cap');
  box(0,roof-.22,.025,w,.11,.20,'damp','Upper wall shadow course');
  for(const side of [-1,1]){
    const x=side*(w/2-.07);box(x,(.8+roof-.2)/2,.10,.30,roof-1,.50,'sunWall','Facade pier');box(x,.96,.12,.40,.25,.60,'damp','Pier foot');box(x,roof-.22,.10,.47,.23,.66,'cornice','Pier capital');
  }
  // Rusted service pipe visible below the movie's two windows.
  const pipe=new T.Mesh(new T.CylinderGeometry(.16,.16,w,24),materials.iron);pipe.name='Continuous rusted service pipe';pipe.rotation.z=Math.PI/2;pipe.position.set(0,.66,.75);pipe.castShadow=pipe.receiveShadow=true;group.add(pipe);
  for(const x of [-w*.37,w*.25]){const rim=new T.Mesh(new T.CylinderGeometry(.19,.19,.075,24),materials.ironEdge);rim.name='Service pipe flange';rim.rotation.z=Math.PI/2;rim.position.set(x,.66,.75);group.add(rim);box(x,.36,.78,.13,.50,.21,'iron','Pipe support');}
  const drain=fit.drainpipe;
  if(drain){
    const q=new T.Mesh(new T.CylinderGeometry(drain.radius,drain.radius,drain.top-drain.bottom,16),materials.ironEdge);q.name='Vertical drainpipe between rectangle and oculus';q.position.set(drain.x,(drain.top+drain.bottom)/2,drain.front);q.castShadow=q.receiveShadow=true;group.add(q);
    for(const y of [1.02,2.48,4.48]){
      const band=new T.Mesh(new T.CylinderGeometry(drain.radius+.018,drain.radius+.018,.066,16),materials.iron);band.name='Drainpipe fixing collar';band.position.set(drain.x,y,drain.front);group.add(band);
      box(drain.x,y,drain.front*.5,.055,.055,drain.front,'iron','Drainpipe wall bracket');
    }
    line([[drain.x,drain.top,drain.front],[drain.x,drain.top+.09,drain.front*.68],[drain.x,drain.top+.09,.03]],drain.radius,'ironEdge','Drainpipe upper bend');
  }
  group.updateMatrixWorld(true);return group;
}
