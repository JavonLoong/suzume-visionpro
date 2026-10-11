// Complete support ring; visible film members and inferred rear ribs are explicit.
function buildMovieSteel25(T,scene,fit,materials){
  const group=new T.Group();group.name='Movie radial steelwork v25';scene.add(group);
  const center=new T.Vector3(fit.centerNative[0],0,-fit.centerNative[1]);
  const point=v=>new T.Vector3(v[0],v[2],-v[1]);
  const circle=(a,r,z)=>new T.Vector3(center.x+Math.sin(a)*r,z,center.z-Math.cos(a)*r);
  const radial=(a,t)=>circle(a,fit.radius*Math.cos(t),fit.springHeight+fit.rise*Math.sin(t));
  const section=(w,d,web,flange)=>[[-w/2,-d/2],[w/2,-d/2],[w/2,-d/2+flange],[web/2,-d/2+flange],[web/2,d/2-flange],[w/2,d/2-flange],[w/2,d/2],[-w/2,d/2],[-w/2,d/2-flange],[-web/2,d/2-flange],[-web/2,-d/2+flange],[-w/2,-d/2+flange]];
  function profiled(points,shape,name,kind,index,mode='bow',angle=0){
    const curve=new T.CatmullRomCurve3(points),length=curve.getLength(),steps=Math.max(1,Math.ceil(length/.20)),p=[],uv=[],faces=[];
    let perimeter=0;const edge=[0];for(let i=1;i<shape.length;i++){perimeter+=new T.Vector2(...shape[i]).distanceTo(new T.Vector2(...shape[i-1]));edge.push(perimeter);}
    const halfPerimeter=perimeter+new T.Vector2(...shape[0]).distanceTo(new T.Vector2(...shape[shape.length-1]));
    for(let j=0;j<=steps;j++){
      const q=curve.getPoint(j/steps),t=curve.getTangent(j/steps).normalize();
      let a,b;
      if(mode==='column'){
        b=q.clone().sub(center);b.y=0;b.normalize();a=new T.Vector3().crossVectors(b,t).normalize();
      }else if(mode==='radial'){
        a=new T.Vector3(Math.cos(angle),0,Math.sin(angle));b=new T.Vector3().crossVectors(t,a).normalize();
      }else{
        a=q.clone().sub(center);a.y=0;a.normalize();a.addScaledVector(t,-a.dot(t)).normalize();b=new T.Vector3().crossVectors(t,a).normalize();if(b.y<0)b.negate();
      }
      for(let k=0;k<shape.length;k++){const v=q.clone().addScaledVector(a,shape[k][0]).addScaledVector(b,shape[k][1]);p.push(v.x,v.y,v.z);uv.push(edge[k]/.35,j/steps*length/.35);}
      if(j<steps)for(let k=0;k<shape.length;k++){const x=j*shape.length+k,y=j*shape.length+(k+1)%shape.length;faces.push(x,y,y+shape.length,x,y+shape.length,x+shape.length);}
    }
    for(const tri of T.ShapeUtils.triangulateShape(shape.map(v=>new T.Vector2(...v)),[])){faces.push(tri[2],tri[1],tri[0]);faces.push(...tri.map(i=>i+steps*shape.length));}
    let g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(p,3));g.setAttribute('uv',new T.Float32BufferAttribute(uv,2));g.setIndex(faces);g=g.toNonIndexed();g.computeVertexNormals();
    const mesh=new T.Mesh(g,materials.steel);mesh.name=name;mesh.userData={kind,index,centerline:points.map(v=>v.toArray()),profile:shape};mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);return mesh;
  }
  function boxAt(a,r,z,w,h,d,mat,name,index){const o=new T.Mesh(new T.BoxGeometry(w,h,d),materials[mat]);o.position.copy(circle(a,r,z));o.rotation.y=-a;o.name=name;o.userData={kind:'connection',index};o.castShadow=o.receiveShadow=true;group.add(o);return o;}
  function rod(points,r,name,index){const curve=new T.CatmullRomCurve3(points);const o=new T.Mesh(new T.TubeGeometry(curve,Math.max(2,Math.ceil(curve.getLength()/.25)),r,8,false),materials.edge);o.name=name;o.userData={kind:'tie',index};o.castShadow=o.receiveShadow=true;group.add(o);return o;}
  const cs=fit.columnSection,bs=fit.beamSection;
  const columnProfile=section(cs.flangeWidth,cs.radialDepth,cs.webThickness,cs.flangeThickness);
  const ribProfile=section(.23,.27,.022,.025);
  const bowProfile=section(bs.radialWidth,bs.verticalDepth,bs.webThickness,bs.flangeThickness);
  for(let i=0;i<fit.angles.length;i++){
    if(fit.removedRibs.includes(i))continue;
    const a=fit.angles[i],measured=fit.mainColumns.find(q=>q.index===i),foot=measured?measured.footingTop:.54;
    profiled([circle(a,fit.radius,foot),circle(a,fit.radius,fit.springHeight)],columnProfile,'I-section support column '+i,'column',i,'column',a);
    boxAt(a,fit.radius,(foot-.05-.22)/2,.43,foot-.05+.22,.43,'concrete','Grounded column footing '+i,i);
    boxAt(a,fit.radius,foot-.035,.38,.04,.34,'edge','Rusted base plate '+i,i);
    for(const x of [-.12,.12])for(const z of [-.105,.105]){
      const bolt=new T.Mesh(new T.CylinderGeometry(.022,.022,.055,6),materials.edge);bolt.position.copy(circle(a,fit.radius,foot-.004));bolt.position.x+=Math.cos(a)*x+Math.sin(a)*z;bolt.position.z+=Math.sin(a)*x-Math.cos(a)*z;bolt.name='Column anchor bolt '+i;bolt.userData={kind:'bolt',index:i};group.add(bolt);
    }
    const end=fit.ends[i];if(end>0){const count=Math.max(3,Math.ceil(end/.065));const pts=Array.from({length:count},(_,j)=>radial(a,end*j/(count-1)));profiled(pts,ribProfile,'Broken radial I-section rib '+i,'rib',i,'radial',a);}
    const next=(i+1)%fit.angles.length,an=fit.angles[next]+(next===0?Math.PI*2:0);
    if(Math.cos(a)<.68&&!fit.removedRibs.includes(next)){
      const pts=Array.from({length:12},(_,j)=>{const t=j/11;return circle(a+(an-a)*t,fit.radius,fit.springHeight-.5+Math.sin(t*Math.PI)*.85);});
      profiled(pts,section(.10,.12,.016,.019),'Surviving side arch '+i,'inferred-side-arch',i);
    }
  }
  for(let ring=0;ring<6;ring++){
    const t=.035+ring*.15;
    for(let i=0;i<fit.angles.length;i++){
      const next=(i+1)%fit.angles.length;if(fit.removedRibs.includes(i)||fit.removedRibs.includes(next)||t>fit.ends[i]||t>fit.ends[next]||((i*7+ring*3)%13===0))continue;
      const a=fit.angles[i],b=fit.angles[next]+(next===0?Math.PI*2:0);rod(Array.from({length:7},(_,j)=>radial(a+(b-a)*j/6,t)),ring===0?.045:.027,'Upper dome ring tie '+ring+' '+i,i);
    }
  }
  fit.bowedBeams.forEach((b,i)=>profiled(b.pointsNative.map(point),bowProfile,b.name,'observed-bow',i));
  fit.slenderTies.forEach((q,i)=>{const bottom=point(q.bottom),top=bottom.clone();top.y=q.topHeight;profiled([bottom,top],section(q.width,q.depth,.009,.009),q.name,'observed-hanger',i,'column');});
  // Ivy grows on the measured columns and bowed steel itself, with modeled
  // petioles. The additional plants have no detached billboard layer.
  let seed=250910;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const leafShape=new T.Shape();[[0,0],[-.24,.19],[-.52,.27],[-.32,.44],[-.40,.66],[-.10,.60],[0,.94],[.15,.62],[.43,.69],[.35,.42],[.53,.29],[.24,.18]].forEach((v,i)=>i?leafShape.lineTo(...v):leafShape.moveTo(...v));leafShape.closePath();
  const leafGeo=new T.ExtrudeGeometry(leafShape,{depth:.012,bevelEnabled:false});
  const la=leafGeo.attributes.position;for(let i=0;i<la.count;i++)la.setZ(i,la.getZ(i)+.055*Math.max(0,1-Math.abs(la.getX(i))*2)*Math.sin(la.getY(i)*Math.PI));leafGeo.computeVertexNormals();
  function ivyTube(points,r,name,index){const curve=new T.CatmullRomCurve3(points);const o=new T.Mesh(new T.TubeGeometry(curve,Math.max(2,Math.ceil(curve.getLength()/.06)),r,6,false),materials.vine);o.name=name;o.userData={kind:'ivy-stem',index};o.castShadow=o.receiveShadow=true;group.add(o);return curve;}
  function leavesOn(curve,count,index,name,offset=.04){
    for(let j=0;j<count;j++){
      const t=(j+.25+random()*.5)/count,stem=curve.getPoint(t),rad=stem.clone().sub(center);rad.y=0;rad.normalize();const a=Math.atan2(rad.x,-rad.z),tangent=new T.Vector3(Math.cos(a),0,Math.sin(a)),side=j%2?1:-1;
      const base=stem.clone().addScaledVector(tangent,side*(offset+random()*.045)).addScaledVector(rad,-.015-random()*.025);base.y+=.008+random()*.035;
      ivyTube([stem,stem.clone().lerp(base,.55).add(new T.Vector3(0,.014,0)),base],.0025,name+' petiole '+j,index);
      const leaf=new T.Mesh(leafGeo,materials['leaf'+Math.floor(random()*3)]);leaf.name=name+' ivy leaf '+j;leaf.position.copy(base);leaf.rotation.set((random()-.5)*.9,-a+(random()-.5)*1.1,side*(.5+random()*.7));leaf.scale.setScalar(.11+random()*.085);leaf.castShadow=leaf.receiveShadow=true;leaf.userData={kind:'ivy-leaf',index,attachedStemNative:[stem.x,-stem.z,stem.y]};group.add(leaf);
    }
  }
  for(const q of fit.mainColumns){
    const a=q.angle,rad=new T.Vector3(Math.sin(a),0,-Math.cos(a)),tangent=new T.Vector3(Math.cos(a),0,Math.sin(a)),end=q.index===27?4.72:6.55;
    const pts=Array.from({length:32},(_,j)=>{const z=q.footingTop+(end-q.footingTop)*j/31;return circle(a,fit.radius,z).addScaledVector(tangent,-.065+.06*Math.sin(z*4.1+q.index)).addScaledVector(rad,-.145-.013*Math.cos(z*3));});
    const curve=ivyTube(pts,.006,'Column climbing ivy '+q.index,q.index);leavesOn(curve,q.index===27?58:78,q.index,'Column '+q.index);
  }
  fit.bowedBeams.forEach((b,i)=>{
    const beamCurve=new T.CatmullRomCurve3(b.pointsNative.map(point));const begin=i===0?.70:.12;
    const pts=Array.from({length:28},(_,j)=>{const p=beamCurve.getPoint(begin+(1-begin)*j/27);const radial=p.clone().sub(center);radial.y=0;radial.normalize();return p.addScaledVector(radial,-.10).add(new T.Vector3(0,.065,0));});
    const curve=ivyTube(pts,.0055,'Bowed beam creeping ivy '+i,i);leavesOn(curve,i===0?18:48,i,'Bowed beam '+i,.02);
  });
  group.updateMatrixWorld(true);return group;
}
