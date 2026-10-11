    const projectionSpec24=__PROJECTION_SPEC_24__,math24=projectionGeometry24(projectionSpec24);
    const fit24=__BAY_FIT_24__,right24=__RIGHT_FIT_24__;
    let removed24=0;
    for(const o of [...scene.children]){
      if(!o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh'))continue;
      const src=o.geometry.index?o.geometry.toNonIndexed():o.geometry,ps=src.attributes.position,keep=[];
      for(let i=0;i<ps.count;i+=3){
        let x=0,z=0;for(let j=0;j<3;j++){x+=ps.getX(i+j)/3;z+=ps.getZ(i+j)/3;}
        const a=Math.atan2(x,-z),r=Math.hypot(x,z);
        if((a>projectionSpec24.oldEdges[12]-1e-5&&a<projectionSpec24.oldEdges[16]+1e-5&&r>19.2)||(a>projectionSpec24.oldEdges[16]-1e-5&&a<projectionSpec24.oldEdges[17]+1e-5&&r>20.5)){removed24++;continue;}
        keep.push(i,i+1,i+2);
      }
      const g=new T.BufferGeometry();for(const [name,attr]of Object.entries(src.attributes)){
        const values=new attr.array.constructor(keep.length*attr.itemSize);for(let i=0;i<keep.length;i++)for(let j=0;j<attr.itemSize;j++)values[i*attr.itemSize+j]=attr.array[keep[i]*attr.itemSize+j];
        g.setAttribute(name,new T.BufferAttribute(values,attr.itemSize,attr.normalized));
      }o.geometry=g;
    }
    function mesh24(o,fn){
      const g=o.geometry.clone(),a=g.attributes.position;
      for(let i=0;i<a.count;i++){const v=fn([a.getX(i),-a.getZ(i),a.getY(i)]);a.setXYZ(i,v[0],v[2],-v[1]);}
      a.needsUpdate=true;g.computeVertexNormals();g.computeBoundingBox();g.computeBoundingSphere();o.geometry=g;
    }
    for(const o of [...scene.children]){
      if(o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh'))mesh24(o,v=>math24.source(v,true));
      else if(o.name.startsWith('Broken radial dome steelwork solid mesh'))mesh24(o,v=>math24.source(v,false));
      else if(o.name.startsWith('Brick and masonry debris solid mesh'))mesh24(o,v=>Math.hypot(v[0],v[1])>8?math24.source(v,false):v);
    }
    const rightMats24={sunWall:sunWall.clone(),cornice:cornice.clone(),damp,roomMat,mullionMat:mullionMat.clone(),iron,ironEdge,windowMat:windowMat.clone()};
    rightMats24.sunWall.color.setHex(0xf1eee6);rightMats24.cornice.color.setHex(0xe9e5d7);rightMats24.mullionMat.color.setHex(0x777562);rightMats24.windowMat.color.setHex(0x213040);
    const groups24=[buildMovieBays23(T,scene,fit24,{stoneMap,rustMap,paintMap,brass,moss}),buildMovieBay21(T,scene,rightMats24,right24)];
    const recolored24=new Set();let parts24=0;
    groups24.forEach((group,gi)=>{
      group.updateMatrixWorld(true);
      group.traverse(o=>{
        if(!o.isMesh)return;
        let index=16;if(!gi){let a=o;while(a&&!Number.isInteger(a.userData.bayIndex23))a=a.parent;index=a.userData.bayIndex23;}
        // Place geometry in world coordinates before baking; cancel its parents.
        o.geometry=o.geometry.clone();o.geometry.applyMatrix4(o.matrixWorld);mesh24(o,v=>math24.newBay(v,index));
        o.matrixAutoUpdate=false;o.matrix.copy(o.parent.matrixWorld).invert();
        if(!gi&&!recolored24.has(o.material)){recolored24.add(o.material);const color=o.material.color.getHex();if(color===0xa0bfd5)o.material.color.setHex(0xe1e4e6);else if(color===0xd7d4bd)o.material.color.setHex(0xe4e5e3);}
      });
      group.name='Movie calibrated rooms v24 group '+gi;parts24+=bake(group);
    });
    root.projectionEvidence24={revision:24,removedTriangles:removed24,newParts:parts24,courtyardRadius:23.5,completeCircle:true,browserRuntimeVerified:false,oneToOneComplete:false};
