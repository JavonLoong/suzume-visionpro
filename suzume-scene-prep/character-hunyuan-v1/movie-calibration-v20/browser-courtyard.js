    // Full geometry variant; the original poster viewer remains separately available.
    const movieFit=__MOVIE_COURTYARD_FIT__,mp=movieFit.parameters,mk=movieFit.depthScale;
    const mc=new T.Vector3(movieFit.depthScaleCenter[0],movieFit.depthScaleCenter[2],-movieFit.depthScaleCenter[1]);
    const mxy=new T.Matrix4().makeTranslation(mp.translateX,0,-mp.translateY).multiply(new T.Matrix4().makeRotationY(-mp.yaw));
    const mdepth=new T.Matrix4().makeTranslation(mc.x,mc.y,mc.z).multiply(new T.Matrix4().makeScale(mk,1,mk)).multiply(new T.Matrix4().makeTranslation(-mc.x,-mc.y,-mc.z));
    const mflat=mdepth.clone().multiply(mxy),mfull=new T.Matrix4().makeScale(1,mk,1).multiply(mflat);
    const mh=z=>{const j=.89,b=-.22,top=mc.y+mk*(j*mp.heightScale+mp.heightOffset-mc.y);return z>=j?mc.y+mk*(z*mp.heightScale+mp.heightOffset-mc.y):b+(z-b)*(top-b)/(j-b);};
    const mpoint=new T.Vector3(),mrot=new T.Quaternion().setFromAxisAngle(new T.Vector3(0,1,0),-mp.yaw);
    function movieMesh(o,kind){
      o.geometry=o.geometry.clone();const a=o.geometry.attributes.position;
      for(let i=0;i<a.count;i++){
        mpoint.fromBufferAttribute(a,i);const rr=Math.hypot(mpoint.x,mpoint.z),oldY=mpoint.y;
        if(kind==='rubble'&&rr<=8)continue;
        mpoint.applyMatrix4(mflat);mpoint.y*=mk;
        if(kind==='hotel'){let t=Math.max(0,Math.min(1,(rr-21.7)/.8));t=t*t*(3-2*t);mpoint.y=oldY*mk*(1-t)+mh(oldY)*t;}
        a.setXYZ(i,mpoint.x,mpoint.y,mpoint.z);
      }
      a.needsUpdate=true;o.geometry.computeVertexNormals();o.geometry.computeBoundingBox();o.geometry.computeBoundingSphere();
    }
    for(const o of [...scene.children]){
      if(o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh'))movieMesh(o,'hotel');
      else if(o.name.startsWith('Brick and masonry debris solid mesh'))movieMesh(o,'rubble');
      else if(o.name.startsWith('Broken radial dome steelwork solid mesh')||['Continuous forest terrain','Branching tree crowns surrounding the ruined hotel','Forest trunks'].includes(o.name))o.applyMatrix4(mfull);
      else if(o===water)o.applyMatrix4(mflat);
      else if(o.name==='Individual three-dimensional ivy leaves'){
        const matrix=new T.Matrix4(),pos=new T.Vector3(),rot=new T.Quaternion(),scale=new T.Vector3();
        for(let i=0;i<o.count;i++){
          o.getMatrixAt(i,matrix);matrix.decompose(pos,rot,scale);if(Math.hypot(pos.x,pos.z)<=8)continue;
          const y=pos.y;pos.applyMatrix4(mflat);pos.y=mh(y);rot.premultiply(mrot);scale.multiplyScalar(mk);
          matrix.compose(pos,rot,scale);o.setMatrixAt(i,matrix);
        }o.instanceMatrix.needsUpdate=true;o.frustumCulled=false;
      }
    }
    const sourceBed=scene.children.find(o=>o.name==='Flooded polygon flagstones and broken slabs solid mesh'&&o.geometry.attributes.position.count===288);
    if(sourceBed){const bed=sourceBed.clone();bed.geometry=sourceBed.geometry.clone();bed.name='Movie courtyard continuous basin bed';bed.applyMatrix4(mflat);bed.position.y-=.04;scene.add(bed);}
    root.movieCourtyardEvidence={revision:20,method:'Complete circular geometry, grounded podium and constrained depth fit',inferredCourtyardRadius:23.5*mk,foregroundPreserved:true,browserRuntimeVerified:false,oneToOneComplete:false};
