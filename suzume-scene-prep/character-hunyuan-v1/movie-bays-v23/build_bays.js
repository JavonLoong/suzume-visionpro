
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
    // Reconstructed topology from the production plan; dimensions remain inferred.
    const hotel=new T.Group();hotel.name='Circular ruined hotel with exterior entrance';scene.add(hotel);
    const R=23.5,N=32,step=Math.PI*2/N,bayWidth=2*R*Math.tan(step/2),bayRecords=[];
    const facadeEdges=Array.from({length:N+1},(_,i)=>(i-N/2-.5)*step);
    const measuredPiers=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];measuredPiers.forEach((a,k)=>facadeEdges[13+k]=a);
    const shadeWall=material(0xa0bfd5,stoneMap,.95),sunWall=material(0xf2e6a6,stoneMap,.95);
    const wallA=material(0xb8c4bc,stoneMap,.95),wallB=material(0xd4d1b8,stoneMap,.97),cornice=material(0xd7d4bd,stoneMap,.92);
    const damp=material(0x708c83,stoneMap,1),recess=material(0x203d43,null,1),windowMat=new T.MeshStandardMaterial({color:0x34576c,roughness:.59,metalness:.12,transparent:true,opacity:.65});
    const mullionMat=material(0xa29c7e,rustMap,.83,.12),brickMat=material(0x996b4e,stoneMap,1),roomMat=material(0x354947,stoneMap,1);
    const iron=material(0x655448,rustMap,.91,.3),ironEdge=material(0xa98962,rustMap,.8,.28);
    const glassMat=new T.MeshStandardMaterial({color:0x7daab2,roughness:.31,metalness:.1,transparent:true,opacity:.16,side:T.DoubleSide});
    const brownDoor=material(0x796359,paintMap,.92),acCase=material(0x9d9f91,rustMap,.93),awningMat=material(0x598b88,stoneMap,.96);
    function roundedOpening(x,y,w,h,rise){const pts=[[x-w/2,y],[x-w/2,y+h-rise]];for(let k=0;k<=20;k++){const a=Math.PI-k*Math.PI/20;pts.push([x+Math.cos(a)*w/2,y+h-rise+Math.sin(a)*rise]);}pts.push([x+w/2,y]);return pts;}
    function circleOpening(x,y,r){return Array.from({length:32},(_,i)=>[x+Math.cos(i*Math.PI/16)*r,y+Math.sin(i*Math.PI/16)*r]);}
    function wallWithOpenings(width,height,holes,mat,parent,depth=.4){
      const shape=new T.Shape();shape.moveTo(-width/2,0);shape.lineTo(width/2,0);shape.lineTo(width/2,height);shape.lineTo(-width/2,height);shape.closePath();
      for(const points of holes){const hole=new T.Path();hole.moveTo(points[0][0],points[0][1]);for(let k=1;k<points.length;k++)hole.lineTo(...points[k]);hole.closePath();shape.holes.push(hole);}
      const g=new T.ExtrudeGeometry(shape,{depth,bevelEnabled:false,curveSegments:10});g.translate(0,0,-depth);
      const u=g.attributes.uv;for(let k=0;k<u.count;k++)u.setXY(k,u.getX(k)*.22,u.getY(k)*.22);
      const mesh=new T.Mesh(g,mat);mesh.castShadow=true;mesh.receiveShadow=true;parent.add(mesh);return mesh;
    }
    function arcRim(x,y,w,h,rise,thick,mat,parent,z=.10){curve(roundedOpening(x,y,w,h,rise).map(p=>[p[0],p[1],z]),thick,mat,parent);}
    function gridWindow(x,y,w,h,parent,arched=false){
      const group=new T.Group();group.position.x=x;parent.add(group);const cols=Math.max(3,Math.round(w/.43));
      const glassShape=new T.Shape();const outline=arched?roundedOpening(0,y,w,h,w/2):[[-w/2,y],[w/2,y],[w/2,y+h],[-w/2,y+h]];
      outline.forEach((p,k)=>k?glassShape.lineTo(...p):glassShape.moveTo(...p));glassShape.closePath();const pane=new T.Mesh(new T.ShapeGeometry(glassShape),windowMat);pane.position.z=-.12;group.add(pane);
      const transom=arched?y+h-w/2:y+h-.40;
      for(let j=0;j<=cols;j++){const xx=-w/2+w*j/cols;box(j%2===0?.058:.028,transom-y,.09,xx,(y+transom)/2,.022,mullionMat,group);}
      for(let j=0;j<=4;j++)box(w,j===4?.07:.032,.09,0,y+(transom-y)*j/4,.03,mullionMat,group);
      if(arched){arcRim(0,y,w,h,w/2,.043,mullionMat,group);for(let j=1;j<6;j++){const a=Math.PI*j/6;beam([0,transom,.03],[Math.cos(a)*w/2,transom+Math.sin(a)*w/2,.03],.027,.04,mullionMat,group);}}
      else{for(const xx of [-w/6,w/6])box(.070,h,.11,xx,y+h/2,.038,mullionMat,group);for(let j=0;j<=cols*2;j++)box(.023,.40,.07,-w/2+w*j/(cols*2),transom+.20,.025,mullionMat,group);box(w,.066,.11,0,y+h,.03,mullionMat,group);}
      for(const xx of [-w/2,w/2])box(.11,h,.16,xx,y+h/2,.005,cornice,group);
      box(w+.20,.13,.31,0,y-.02,.09,cornice,group);
      // Dark room divisions remain behind the glazing in all viewing directions.
      for(let j=0;j<cols;j++)if(rand()<.27)box(w/cols-.05,(transom-y)*range(.35,.9),.06,-w/2+(j+.5)*w/cols,y+(transom-y)*.42,-.55,roomMat,group);
    }
    function oculus(x,y,r,parent){
      const glass=new T.Mesh(new T.CircleGeometry(r,32),windowMat);glass.position.set(x,y,-.15);parent.add(glass);
      curve([...circleOpening(x,y,r),circleOpening(x,y,r)[0]].map(p=>[p[0],p[1],.035]),.065,cornice,parent);
      const inner=new T.Mesh(new T.TorusGeometry(r*.35,.025,5,20),mullionMat);inner.position.set(x,y,.02);parent.add(inner);
      for(let j=0;j<8;j++){const a=j*Math.PI/4;beam([x,y,.025],[x+Math.cos(a)*r,y+Math.sin(a)*r,.025],.025,.04,mullionMat,parent);}
    }
    function portalEntrance(parent,opened){
      const frame=new T.Group();frame.position.z=.30;frame.scale.set(.83,.87,1);parent.add(frame);
      wallWithOpenings(3.12,3.86,[roundedOpening(0,.72,2.34,3.05,1.12)],wallA,frame,.34);
      box(3.40,.19,.74,0,3.92,-.03,cornice,frame);box(3.62,.095,.82,0,4.065,-.03,cornice,frame);
      for(const s of [-1,1]){box(.28,3.16,.48,s*1.40,2.12,.03,cornice,frame);box(.42,.25,.56,s*1.40,.78,.05,damp,frame);box(.36,.22,.57,s*1.40,3.76,.04,cornice,frame);}
      arcRim(0,.70,2.44,3.16,1.16,.065,cornice,frame,.12);
      const spring=2.65;for(let j=0;j<=10;j++){const a=Math.PI*j/10;beam([0,spring,-.02],[Math.cos(a)*1.10,spring+Math.sin(a)*1.10,-.02],.031,.05,mullionMat,frame);}
      box(2.32,.08,.11,0,spring,-.02,mullionMat,frame);
      for(const s of [-1,1]){
        const leaf=new T.Group();leaf.position.set(s*1.13,.77,-.11);if(opened&&s<0)leaf.rotation.y=-.83;frame.add(leaf);
        box(1.10,1.83,.09,-s*.55,.915,0,brownDoor,leaf);box(.81,.73,.014,-s*.55,1.40,.052,windowMat,leaf);
        for(let j=0;j<5;j++)box(.023,.75,.03,-s*.55-.35+j*.175,1.40,.067,mullionMat,leaf);
        for(let j=0;j<4;j++)box(.80,.023,.03,-s*.55,1.09+j*.20,.067,mullionMat,leaf);
        for(const xx of [-.43,.43])box(.04,.66,.02,-s*.55+xx,.44,.057,mullionMat,leaf);
        box(.83,.04,.02,-s*.55,.10,.057,mullionMat,leaf);box(.83,.04,.02,-s*.55,.77,.057,mullionMat,leaf);
        box(.025,.20,.035,-s*1.0,1.01,.09,brass,leaf);
      }
      for(let j=0;j<5;j++)box(2.13,.16,.48+j*.24,0,.66-j*.135,.55+j*.12,damp,frame);
      for(const s of [-1,1]){const rail=box(.22,.46,1.58,s*1.14,.43,.93,cornice,frame);rail.rotation.x=-.16;}
    }
    function acUnit(x,y,z,angle,parent){
      const ac=new T.Group();ac.position.set(x,y,z);ac.rotation.set(.05,angle,.14);parent.add(ac);box(.86,.66,.39,0,.33,0,acCase,ac);
      box(.51,.51,.025,-.10,.33,.208,iron,ac);for(let j=0;j<11;j++){box(.48,.017,.021,-.10,.105+j*.045,.227,mullionMat,ac);box(.013,.48,.022,-.33+j*.046,.34,.23,mullionMat,ac);}
      cylinder(.21,.21,.018,-.10,.34,.219,recess,ac).rotation.x=Math.PI/2;box(.12,.05,.013,.29,.50,.21,iron,ac);
      for(const xx of [-.29,.29])box(.11,.05,.45,xx,-.01,0,iron,ac);
    }
    function railing(w,y,parent){
      box(w,.048,.075,0,y+.70,-.02,mullionMat,parent);box(w,.047,.08,0,y+.10,-.02,mullionMat,parent);
      for(let j=0;j<=Math.floor(w/.20);j++)box(.028,.64,.047,-w/2+j*w/Math.floor(w/.20),y+.40,-.02,mullionMat,parent);
    }
    function ringSlab(frontZ,backZ,topY,thickness,mat,parent){
      const shape=new T.Shape(),fw=(parent.userData.chordRadius-frontZ)*Math.tan(parent.userData.halfAngle)+.012,bw=(parent.userData.chordRadius-backZ)*Math.tan(parent.userData.halfAngle)+.012;
      shape.moveTo(-fw,frontZ);shape.lineTo(fw,frontZ);shape.lineTo(bw,backZ);shape.lineTo(-bw,backZ);shape.closePath();
      const g=new T.ExtrudeGeometry(shape,{depth:thickness,bevelEnabled:false}),o=new T.Mesh(g,mat);o.rotation.x=Math.PI/2;o.position.y=topY;o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;
    }
    function tank(x,z,r,h,y,parent){
      const t=new T.Group();t.position.set(x,y,z);parent.add(t);cylinder(r,r,h,0,h/2,0,acCase,t);
      for(const yy of [.08,h*.50,h-.07]){const rim=new T.Mesh(new T.TorusGeometry(r+.015,.034,5,32),cornice);rim.rotation.x=Math.PI/2;rim.position.y=yy;t.add(rim);}
      const cap=new T.Mesh(new T.SphereGeometry(r,24,8,0,Math.PI*2,0,Math.PI/2),acCase);cap.scale.y=.28;cap.position.y=h;t.add(cap);
      for(const s of [-1,1])beam([s*.23,.1,r+.13],[s*.23,h+.37,r+.13],.033,.055,iron,t);
      for(let j=0;j<h/.27;j++)box(.50,.026,.042,0,j*.27+.1,r+.13,iron,t);
      curve([[r*.78,.1,0],[r+.3,.1,0],[r+.3,.8,0]],.05,iron,t);
    }
    // The south gap is bounded by glazed entrance wings; the rest has solid rooms.
    const types={3:'glass',4:'glass',5:'wide',6:'wide',7:'portico',8:'wide',9:'wide',10:'oculus',11:'wide',12:'wide',13:'archside',14:'portico',15:'wide',16:'wide',17:'portico',18:'mixed',19:'wide',20:'wide',21:'wide',22:'wide',23:'portico',24:'wide',25:'wide',26:'arch',27:'wide',28:'glass',29:'glass'};
    for(const spec of fit.bays){ const i=spec.index;
      const a0=facadeEdges[i],a1=facadeEdges[i+1],span=a1-a0,angle=(a0+a1)/2,type=spec.openings.length?'movie-fit':(types[i]||'entrance-gap'),half=span/2,chordR=R*Math.cos(half);
      const bay=new T.Group();bay.name='Hotel bay '+i+' '+type;bay.userData.bayIndex23=i;bay.position.set(Math.sin(angle)*chordR,0,-Math.cos(angle)*chordR);bay.userData.halfAngle=half;bay.userData.chordRadius=chordR;bay.rotation.y=-angle;hotel.add(bay);
      bayRecords.push({index:i,angle,edges:[a0,a1],center:bay.position.toArray(),type});const w=2*R*Math.sin(half)+.022,wmat=i>=11&&i<=15?shadeWall:i>=18&&i<=23?sunWall:i%3===0?wallA:wallB;
      if(type==='entrance-gap'){
        for(let j=0;j<6;j++)box(w,.15,3.4+j*.40,0,.68-j*.13,-1.20,cornice,bay);
        continue;
      }
      const leftUpper=i>=7&&i<=15,rightUpper=i>=18&&i<=26,raised=leftUpper||rightUpper,roofY=leftUpper?6.52:rightUpper?5.86:4.78;
      ringSlab(.26,-4.53,.73,.95,damp,bay);ringSlab(.50,-4.55,.865,.19,cornice,bay);
      if(type==='glass'){
        for(const xx of [-w/2,w/2])box(.23,4.88,.38,xx,3.13,.03,wmat,bay);
        for(let k=0;k<=5;k++)box(.038,4.39,.075,-w/2+w*k/5,2.94,0,mullionMat,bay);
        box(w,.14,.24,0,3.93,0,cornice,bay);box(w,.16,.29,0,5.18,0,cornice,bay);
        arcRim(0,3.93,w-.22,1.18,1.18,.043,iron,bay);
        for(let j=0;j<5;j++)if(rand()>.32)box(w/5-.055,2.92,.017,-w/2+(j+.5)*w/5,2.34,-.034,glassMat,bay);
        for(let j=0;j<6;j++)box(w,.17,3.8+j*.35,0,.76-j*.13,1.2,cornice,bay);
        ringSlab(.30,-4.41,5.365,.17,cornice,bay);
      }else{
        const holes=[];
        if(type==='movie-fit')holes.push(...spec.openings.map(fittedOutline));
        else if(type==='portico')holes.push(roundedOpening(0,.6264,1.9754,2.6709,.9744));
        else if(type==='archside'){holes.push(roundedOpening(w*.26,1.22,1.00,2.14,.5));holes.push([[-w*.48,1.22],[-w*.04,1.22],[-w*.04,3.36],[-w*.48,3.36]]);}
        else if(type==='mixed'){holes.push(roundedOpening(-w*.29,1.22,.97,2.07,.485));holes.push([[-w*.04,1.20],[w*.43,1.20],[w*.43,3.49],[-w*.04,3.49]]);}
        else if(type==='arch')holes.push(roundedOpening(-.35,.99,1.34,2.78,.67));
        else if(type==='oculus')holes.push(circleOpening(-.55,2.92,.43));
        else holes.push([[-w*.42,1.22],[w*.42,1.22],[w*.42,3.36],[-w*.42,3.36]]);
        const lowerWall=wallWithOpenings(w,raised?4.64:roofY-.20,holes,wmat,bay,.46);lowerWall.name='Lower story wall';lowerWall.userData.geometryRole23='lowerWall';
        const backHeight=leftUpper?roofY-.92:rightUpper?4.15:roofY-.90;box(w,backHeight,.32,0,.80+backHeight/2,-4.52,roomMat,bay);
        for(const side of [-1,1]){const wall=box(.22,roofY-.9,4.6/Math.cos(half),side*(w/2+2.3*Math.tan(half)-.05),(roofY+.8)/2,-2.30,wmat,bay);wall.rotation.y=-side*half;}
        box(w,.18,4.8,0,roofY-.22,-2.16,roomMat,bay);
        if(type==='movie-fit')spec.openings.forEach(q=>fittedWindow(q,bay));
        else if(type==='portico')portalEntrance(bay,i===17||i===23);
        else if(type==='archside'){gridWindow(w*.26,1.22,1.00,2.14,bay,true);gridWindow(-w*.26,1.22,w*.44,2.14,bay);}
        else if(type==='mixed'){gridWindow(-w*.29,1.22,.97,2.07,bay,true);gridWindow(w*.195,1.20,w*.47,2.29,bay);}
        else if(type==='arch'){gridWindow(-.35,.99,1.34,2.78,bay,true);box(.05,3.2,.065,w*.30,2.32,.20,iron,bay);}
        else if(type==='oculus')oculus(-.55,2.92,.43,bay);
        else gridWindow(0,1.22,w*.84,2.14,bay);
        if(['wide','mixed','archside'].includes(type)){const awningW=type==='mixed'?w*.51:type==='archside'?w*.46:w*.89,awningX=type==='mixed'?w*.195:type==='archside'?-w*.26:0;box(awningW,.14,.49,awningX,type==='mixed'?3.64:3.51,.16,cornice,bay);box(awningW*.99,.045,.56,awningX,type==='mixed'?3.71:3.58,.20,damp,bay);}
        for(const yy of [4.14,4.39])box(w,.11,yy===4.14?.69:.55,0,yy,.035,yy===4.14?cornice:damp,bay);
        if(raised){
          const upper=new T.Group();upper.position.y=4.66;bay.add(upper);const cutouts=[];
          const count=leftUpper?Math.max(6,Math.round(w/.53)):Math.max(5,Math.round(w/.71));
          for(let j=0;j<count;j++){
            const tall=!leftUpper||j%5>1,ow=leftUpper?(tall?.41:.25):w/count*.88,oh=leftUpper?(tall?.70:.31):.89;
            const xx=-w/2+(j+.5)*w/count;cutouts.push(roundedOpening(xx,0,ow,oh,ow/2));
            arcRim(xx,0,ow+.015,oh+.018,ow/2,.025,cornice,upper,.035);
            if(leftUpper){const sh=new T.Shape();roundedOpening(xx,0,ow,oh,ow/2).forEach((v,k)=>k?sh.lineTo(...v):sh.moveTo(...v));sh.closePath();const glass=new T.Mesh(new T.ShapeGeometry(sh),windowMat);glass.position.z=-.15;upper.add(glass);}
          }
          wallWithOpenings(w,leftUpper?.98:1.10,cutouts,cornice,upper,.26);
          box(w,.095,.51,0,4.67,.02,cornice,bay);
          if(leftUpper){
            const high=new T.Group();high.position.y=5.64;bay.add(high);const apertures=[];
            if(i===15){apertures.push(circleOpening(w*.19,.39,.25));}
            else if(i===12||i===13){for(let j=0;j<4;j++){const xx=-w*.37+j*w*.245;apertures.push([[xx-.38,.14],[xx+.38,.14],[xx+.38,.64],[xx-.38,.64]]);}}
            wallWithOpenings(w,.78,apertures,wallA,high,.35);
            if(i===15)oculus(w*.19,6.03,.25,bay);
            else if(i===12||i===13){for(let j=0;j<4;j++){const xx=-w*.37+j*w*.245;box(.76,.50,.018,xx,6.03,-.09,glassMat,bay);for(const ss of [-1,1])box(.038,.54,.06,xx+ss*.40,6.03,.02,mullionMat,bay);box(.80,.042,.075,xx,5.77,.02,mullionMat,bay);box(.80,.042,.075,xx,6.29,.02,mullionMat,bay);}}
            box(w,.075,.48,0,5.63,.03,damp,bay);
            railing(w,roofY+.02,bay);
          }
        }
        ringSlab(.355,-4.595,roofY+.08,.16,cornice,bay);box(w,.085,.70,0,roofY+.11,.08,cornice,bay);
        box(w,.57,.27,0,roofY+.34,-4.50,wmat,bay);
        for(const s of [-1,1]){
          box(.30,3.5,.50,s*(w/2-.07),2.52,.10,wmat,bay);box(.40,.25,.60,s*(w/2-.07),.96,.12,damp,bay);
          box(.47,.23,.66,s*(w/2-.07),4.27,.10,cornice,bay);
          for(let j=0;j<4;j++)box(.035,.35,.025,s*(w/2-.07)-.12+j*.08,4.02,.36,recess,bay);
        }
        // Water tanks and service sheds occupy specific roof bays, not a repeated motif.
        if([11,14,19,25].includes(i))tank(i===14?1.14:i===19?-1.32:.6,-1.30,i===14?.72:.66,i===14?1.24:1.16,roofY+.10,bay);
        if([12,13,15,18,22,26].includes(i)){
          const hh=[12,13,15].includes(i)?1.60:.57,sw=i===13?2.9:i===15?2.75:2.32;box(sw,hh,1.80,-.12,roofY+hh/2,-1.70,wallA,bay);box(sw+.16,.13,1.98,-.12,roofY+hh+.05,-1.70,cornice,bay);
          for(const xx of [-sw*.4,sw*.4])box(.042,hh+.12,.08,xx-.12,roofY+hh*.50,-.75,iron,bay);for(const xx of [-.29,.29])beam([xx,roofY+.04,-.70],[xx,roofY+hh+.22,-.70],.029,.045,iron,bay);for(let j=0;j<hh/.25;j++)box(.62,.024,.035,0,roofY+j*.25+.05,-.69,iron,bay);
          curve([[.9,roofY+.05,-2.2],[.9,roofY+1.15,-2.2],[1.13,roofY+1.33,-2.2]],.06,iron,bay);
        }
        if(type==='portico'){acUnit(1.86,.80,.80,-.21,bay);acUnit(2.18,.23,1.63,.13,bay);}
        if(i%3===0){
          cylinder(.19,.19,w,0,.66,.75,iron,bay).rotation.z=Math.PI/2;
          for(const xx of [-w*.3,w*.25])cylinder(.23,.23,.08,xx,.66,.75,ironEdge,bay).rotation.z=Math.PI/2;
          curve([[w*.40,.67,.75],[w*.40,1.02,.75],[w*.40,1.02,.30]],.075,iron,bay);
        }
      }
      if(i%4===2){cylinder(.062,.062,4.1,w*.43,2.94,.38,iron,bay);curve([[w*.43,.94,.38],[w*.43,.58,.48],[w*.35,.49,.74]],.062,iron,bay);}
      // Vines spread along ledges and descend in distinct, unequal trails.
      bay.updateMatrixWorld(true);
      for(let k=0;k<5;k++){const p=new T.Vector3(range(-w*.44,w*.44),roofY+range(-.08,.16),.36).applyMatrix4(bay.matrixWorld);foliageSites.push([p.x,p.y,p.z,range(.20,.42)]);}
      if(i%3===1){const xx=range(-w*.35,w*.35);const points=[];for(let k=0;k<6;k++){const p=new T.Vector3(xx+Math.sin(k*1.9)*.10,roofY-k*.62,.36).applyMatrix4(bay.matrixWorld);points.push(p.toArray());foliageSites.push([p.x,p.y,p.z,.14]);}const stem23=curve(points,.012,moss,hotel);stem23.userData.bayIndex23=i;stem23.name="Ivy stem";}
      for(let k=0;k<3;k++){const p=new T.Vector3(range(-w*.45,w*.45),.83,range(.7,1.55)).applyMatrix4(bay.matrixWorld);foliageSites.push([p.x,p.y,p.z,range(.35,.74)]);}
    }

    hotel.name="Movie rebuilt left and central bays v23";hotel.updateMatrixWorld(true);return hotel;
}
