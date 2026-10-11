    const angle24=projectionSpec24.rotationAngle;
    const rigid24=new T.Matrix4().makeTranslation(math24.center[0],0,-math24.center[1]).multiply(new T.Matrix4().makeRotationY(-angle24));
    for(const o of [...scene.children]){
      if(['Continuous forest terrain','Branching tree crowns surrounding the ruined hotel','Forest trunks'].includes(o.name)||o===water)o.applyMatrix4(rigid24);
      if(o.name==='Individual three-dimensional ivy leaves'){
        const m=new T.Matrix4(),pos=new T.Vector3(),rot=new T.Quaternion(),scale=new T.Vector3(),spin=new T.Quaternion();
        for(let i=0;i<o.count;i++){
          o.getMatrixAt(i,m);m.decompose(pos,rot,scale);if(Math.hypot(pos.x,pos.z)<=8)continue;
          const old=Math.atan2(pos.x,-pos.z),v=math24.source([pos.x,-pos.z,pos.y],true),now=Math.atan2(v[0]-math24.center[0],v[1]-math24.center[1]);
          pos.set(v[0],v[2],-v[1]);spin.setFromAxisAngle(new T.Vector3(0,1,0),-(now-old));rot.premultiply(spin);m.compose(pos,rot,scale);o.setMatrixAt(i,m);
        }o.instanceMatrix.needsUpdate=true;o.frustumCulled=false;
      }
    }
    const bed24=scene.children.find(o=>o.name==='Flooded polygon flagstones and broken slabs solid mesh'&&o.geometry.attributes.position.count===288);
    if(bed24){const copy=bed24.clone();copy.geometry=bed24.geometry.clone();copy.name='Movie courtyard continuous basin bed';copy.applyMatrix4(rigid24);copy.position.y-=.04;scene.add(copy);}
    function nightDrop24(x,z){const depth=-z;let t=Math.max(0,Math.min(1,(depth-12)/28));t=t*t*(3-2*t);return 16.8*Math.exp(-Math.pow((depth-116)/39,2))*(.78+.22*Math.pow(Math.sin(x*.024+.8),2))*t;}
    for(const o of nightScene.children){
      if(o.name==='Rolling meadow ground'){
        o.geometry=o.geometry.clone();const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++)a.setY(i,a.getY(i)-nightDrop24(a.getX(i),a.getZ(i)));a.needsUpdate=true;o.geometry.computeVertexNormals();
      }else if(['Individual meadow flowers','Modeled flower stems','Spatial grass blades'].includes(o.name)){
        const m=new T.Matrix4();for(let i=0;i<o.count;i++){o.getMatrixAt(i,m);m.elements[13]-=nightDrop24(m.elements[12],m.elements[14]);o.setMatrixAt(i,m);}o.instanceMatrix.needsUpdate=true;o.frustumCulled=false;
      }else if(o.name.startsWith('Spatial twilight cloud volume ')){
        o.position.y*=.25;o.scale.y*=.25;o.material.uniforms.uCenter.value.copy(o.position);o.material.uniforms.uScale.value.copy(o.scale);
      }
    }
    T.RectAreaLightUniformsLib.init();
    for(const q of __LIGHTS_24__){
      let light;if(q.type==='AREA')light=new T.RectAreaLight(0xffffff,q.powerWatts/(Math.PI*q.dimensions[0]*q.dimensions[1]),...q.dimensions);
      else{light=new T.SpotLight(0xffffff,q.powerWatts/400,20,q.angleRadians,.15,2);light.castShadow=true;light.shadow.mapSize.set(1024,1024);light.shadow.camera.near=.1;light.shadow.camera.far=20;}
      light.name=q.name;light.color.setRGB(...q.color);light.position.set(q.position[0],q.position[2],-q.position[1]);
      if(light.isSpotLight){light.target.position.set(q.target[0],q.target[2],-q.target[1]);scene.add(light.target);}else light.lookAt(q.target[0],q.target[2],-q.target[1]);scene.add(light);
    }
