    const movieBayFit23=__MOVIE_BAY_FIT_23__;
    const movieBayLo23=movieBayFit23.bays[0].edges[0],movieBayHi23=movieBayFit23.bays[movieBayFit23.bays.length-1].edges[1];
    let movieRemovedFaces23=0;
    // Run before adding the separate v21/v22 right bay. The new left group
    // gets its own prefix, so the right-bay replacement cannot cut its edges.
    for(const o of [...scene.children]){
      if(!o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh'))continue;
      const source=o.geometry.index?o.geometry.toNonIndexed():o.geometry,positions=source.attributes.position,keep=[];
      for(let i=0;i<positions.count;i+=3){
        let x=0,z=0;for(let j=0;j<3;j++){x+=positions.getX(i+j)/3;z+=positions.getZ(i+j)/3;}
        const angle=Math.atan2(x,-z),radius=Math.hypot(x,z);
        if(angle>movieBayLo23-1e-5&&angle<movieBayHi23+1e-5&&radius>19.2){movieRemovedFaces23++;continue;}
        keep.push(i,i+1,i+2);
      }
      const geometry=new T.BufferGeometry();
      for(const [name,attribute]of Object.entries(source.attributes)){
        const values=new attribute.array.constructor(keep.length*attribute.itemSize);
        for(let i=0;i<keep.length;i++)for(let j=0;j<attribute.itemSize;j++)values[i*attribute.itemSize+j]=attribute.array[keep[i]*attribute.itemSize+j];
        geometry.setAttribute(name,new T.BufferAttribute(values,attribute.itemSize,attribute.normalized));
      }
      geometry.computeBoundingSphere();o.geometry=geometry;
    }
    const movieBays23=buildMovieBays23(T,scene,movieBayFit23,{stoneMap,rustMap,paintMap,brass,moss});
    const movieBayMaterials23=new Set();
    movieBays23.traverse(o=>{
      if(!o.isMesh||movieBayMaterials23.has(o.material))return;
      movieBayMaterials23.add(o.material);
      const color=o.material.color.getHex();
      if(color===0xa0bfd5)o.material.color.setHex(0xe1e4e6);
      else if(color===0xd7d4bd)o.material.color.setHex(0xe4e5e3);
    });
    const movieAddedParts23=bake(movieBays23);
    root.movieBayEvidence23={revision:23,bays:[12,13,14,15],newParts:movieAddedParts23,
      removedTriangles:movieRemovedFaces23,measuredLowerWindows:6,completeRoomGeometry:true,
      upperLevelsNeedFurtherCalibration:true,browserRuntimeVerified:false,oneToOneComplete:false};
