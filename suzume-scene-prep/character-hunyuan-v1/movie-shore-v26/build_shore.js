// All surfaces are closed solids, including exposed open pipe bores.
function buildMovieShore26(T,scene,fit,materials){
  const group=new T.Group();group.name='Movie broken waterfront and pipework v26';scene.add(group);
  const point=p=>new T.Vector3(p[0],p[2],-p[1]);
  const circle=(a,r,z)=>point([fit.centerNative[0]+r*Math.sin(a),fit.centerNative[1]+r*Math.cos(a),z]);
  const add=(g,role,name,kind)=>{if(g.index)g=g.toNonIndexed();g.computeVertexNormals();const o=new T.Mesh(g,materials[role]);o.name=name;o.userData={kind,role};o.castShadow=o.receiveShadow=true;group.add(o);return o;};
  function solid(native,bottom,name,role='concrete',kind='slab'){
    // Earcut handles concave shore edges; top vertices retain individual heights.
    const outline=native.map(p=>new T.Vector2(p[0],p[1]));
    const tris=T.ShapeUtils.triangulateShape(outline,[]),p=[],f=[],n=native.length;
    for(const z of [null,bottom])for(const v of native)p.push(v[0],z===null?v[2]:z,-v[1]);
    for(const t of tris){f.push(...t);f.push(t[2]+n,t[1]+n,t[0]+n);}
    // Normalize orientation from the original XY outline rather than trusting
    // input contour winding or earcut's implementation-specific orientation.
    const area=native.reduce((s,a,i)=>{const b=native[(i+1)%n];return s+a[0]*b[1]-a[1]*b[0];},0);
    for(let i=0;i<n;i++){const j=(i+1)%n;if(area>0)f.push(i,i+n,j+n,i,j+n,j);else f.push(i,j+n,i+n,i,j,j+n);}
    const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(p,3));g.setIndex(f);return add(g,role,name,kind);
  }
  for(const q of fit.slabs)solid(q.pointsNative,q.bottom,q.name);
  // Complete annular bank, split into editable sectors. The entrance stays open.
  const bank=fit.bank,segments=112;
  for(let i=0;i<segments;i++){
    const a=i*Math.PI*2/segments,b=(i+1)*Math.PI*2/segments,mid=(a+b)/2;
    if(mid>2.53&&mid<3.85)continue;
    const r0=bank.innerRadius+.08*Math.sin(i*2.17),r1=bank.innerRadius+.08*Math.sin((i+1)*2.17);
    const points=[[a,bank.outerRadius],[b,bank.outerRadius],[b,r1],[a,r0]].map(([t,r])=>{const q=circle(t,r,bank.height);return[q.x,-q.z,q.y];});
    solid(points,bank.bottom,'Annular bank sector '+i,'bank','bank');
    const curb=[[a,bank.curbRadius+bank.curbWidth/2],[b,bank.curbRadius+bank.curbWidth/2],[b,bank.curbRadius-bank.curbWidth/2],[a,bank.curbRadius-bank.curbWidth/2]].map(([t,r])=>{const q=circle(t,r,bank.curbTop);return[q.x,-q.z,q.y];});
    solid(curb,bank.height-.03,'Cracked bank back curb '+i,'curb','curb');
  }
  function pipe(points,r,wall,name,role='rust',kind='pipe'){
    const curve=new T.CatmullRomCurve3(points),length=curve.getLength(),steps=Math.max(4,Math.ceil(length/.12)),radial=16,p=[],faces=[];
    const frames=curve.computeFrenetFrames(steps,false),ring=radial*2;
    for(let j=0;j<=steps;j++){
      const q=curve.getPointAt(j/steps);
      for(const radius of [r,r-wall])for(let k=0;k<radial;k++){
        const a=k*Math.PI*2/radial,v=q.clone().addScaledVector(frames.normals[j],radius*Math.cos(a)).addScaledVector(frames.binormals[j],radius*Math.sin(a));p.push(v.x,v.y,v.z);
      }
    }
    for(let j=0;j<steps;j++)for(let k=0;k<radial;k++){
      const a=j*ring+k,b=j*ring+(k+1)%radial;
      faces.push(a,b,b+ring,a,b+ring,a+ring);
      const c=a+radial,d=b+radial;faces.push(c,d+ring,d,c,c+ring,d+ring);
    }
    for(let k=0;k<radial;k++){
      const a=k,b=(k+1)%radial;faces.push(a,b+radial,b,a,a+radial,b+radial);
      const c=a+steps*ring,d=b+steps*ring;faces.push(c,d,d+radial,c,d+radial,c+radial);
    }
    const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(p,3));g.setIndex(faces);const o=add(g,role,name,kind);o.userData.boreRadius=r-wall;o.userData.centerline=points.map(p=>p.toArray());return curve;
  }
  function bands(curve,r,name){
    const length=curve.getLength(),count=Math.floor(length/1.35);
    for(let k=0;k<=count;k++){
      const t=(k+.35)/(count+1),q=curve.getPointAt(t),tangent=curve.getTangentAt(t).normalize(),normal=new T.Vector3(0,1,0);
      if(Math.abs(normal.dot(tangent))>.94)normal.set(1,0,0);normal.addScaledVector(tangent,-normal.dot(tangent)).normalize();const binormal=new T.Vector3().crossVectors(tangent,normal).normalize();
      const band=pipe([q.clone().addScaledVector(tangent,-.028),q.clone().addScaledVector(tangent,.028)],r+.028,.028,name+' collar '+k,'rustDark','collar');
      for(const side of [-1,1]){
        const bolt=new T.Mesh(new T.CylinderGeometry(.027,.027,.04,6),materials.rustDark);bolt.position.copy(q).addScaledVector(normal,side*(r+.025));bolt.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),normal.clone().multiplyScalar(side));bolt.name=name+' collar bolt '+k+' '+side;bolt.userData={kind:'bolt',role:'rustDark'};bolt.castShadow=bolt.receiveShadow=true;group.add(bolt);
      }
    }
  }
  for(const q of fit.observedPipes){const curve=pipe(q.pointsNative.map(point),q.radius,q.wall,q.name);bands(curve,q.radius,q.name);}
  // Continue the concealed rear/sides coherently; exposed front breaks stay open.
  for(let i=0;i<40;i++){
    const a=i*Math.PI/20,b=(i+1)*Math.PI/20,mid=(a+b)/2;
    if(mid<.55||mid>Math.PI*2-.60||(mid>2.53&&mid<3.85))continue;
    for(const [z,r] of [[.86,.245],[1.36,.135]]){
      const curve=pipe(Array.from({length:5},(_,j)=>circle(a+(b-a)*j/4,fit.pipeRadius,z)),r,.024,'Rear continuation '+i+' '+z);bands(curve,r,'Rear continuation '+i+' '+z);
    }
  }
  group.updateMatrixWorld(true);return group;
}
