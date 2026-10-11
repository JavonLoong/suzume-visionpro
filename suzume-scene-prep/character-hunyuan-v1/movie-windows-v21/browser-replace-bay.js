    const movieWindowFit21=__MOVIE_WINDOW_FIT_21__;
    let removedMovieFaces21=0;
    for(const o of [...scene.children]){
      if(!o.name.startsWith('Circular ruined hotel with exterior entrance solid mesh'))continue;
      const src=o.geometry.index?o.geometry.toNonIndexed():o.geometry,ps=src.attributes.position,keep=[];
      for(let i=0;i<ps.count;i+=3){
        let x=0,z=0;for(let j=0;j<3;j++){x+=ps.getX(i+j)/3;z+=ps.getZ(i+j)/3;}
        const angle=Math.atan2(x,-z),r=Math.hypot(x,z);
        if(angle>movieWindowFit21.edges[0]-1e-5&&angle<movieWindowFit21.edges[1]+1e-5&&r>20.5){removedMovieFaces21++;continue;}
        keep.push(i,i+1,i+2);
      }
      const geo=new T.BufferGeometry();
      for(const [name,attr]of Object.entries(src.attributes)){
        const values=new attr.array.constructor(keep.length*attr.itemSize);
        for(let i=0;i<keep.length;i++)for(let j=0;j<attr.itemSize;j++)values[i*attr.itemSize+j]=attr.array[keep[i]*attr.itemSize+j];
        geo.setAttribute(name,new T.BufferAttribute(values,attr.itemSize,attr.normalized));
      }geo.computeBoundingSphere();o.geometry=geo;
    }
    const newMovieBay21=buildMovieBay21(T,scene,{sunWall,cornice,damp,roomMat,mullionMat,iron,ironEdge,windowMat},movieWindowFit21);
    newMovieBay21.name='Circular ruined hotel with exterior entrance';const addedMovieParts21=bake(newMovieBay21);
    root.movieWindowEvidence21={revision:21,removedTriangles:removedMovieFaces21,newParts:addedMovieParts21,actualWallOpenings:true,reference:'Opening movie still',oneToOneComplete:false,browserRuntimeVerified:false};
