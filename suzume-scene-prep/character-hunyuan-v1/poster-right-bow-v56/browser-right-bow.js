async function applyPosterRightBow56(T,scene,root){
  const [metaResponse,binResponse]=await Promise.all([fetch('../poster-right-bow-v56/browser-right-bow-v56.json'),fetch('../poster-right-bow-v56/right-bow-v56.bin')]);
  if(!metaResponse.ok||!binResponse.ok)throw Error('Right bowed beam v56 could not be loaded');
  const spec=await metaResponse.json(),buffer=await binResponse.arrayBuffer(),targets=new Map();
  for(const q of spec.targets){const mesh=scene.getObjectByName(q.name);if(!mesh||!mesh.isMesh)throw Error('Missing prior steel: '+q.name);targets.set(q.key,mesh);}
  const atlas=await new Promise((resolve,reject)=>new T.TextureLoader().load('../poster-right-bow-v56/'+spec.atlasFile,resolve,undefined,reject));atlas.encoding=T.sRGBEncoding;atlas.anisotropy=8;atlas.wrapS=atlas.wrapT=T.ClampToEdgeWrapping;
  const paint=new T.MeshBasicMaterial({map:atlas,toneMapped:false,fog:false});paint.name='Poster measured beam paint v56';
  const surfaceUpdates=await Promise.all(spec.surfaceUpdates.map(async q=>{
    const mesh=scene.getObjectByName(q.browserTarget);if(!mesh||!mesh.isMesh)throw Error('Missing surface to restore: '+q.browserTarget);
    const map=await new Promise((resolve,reject)=>new T.TextureLoader().load('../poster-right-bow-v56/'+q.newAtlas,resolve,undefined,reject));map.encoding=T.sRGBEncoding;map.anisotropy=8;
    const material=mesh.material.clone();material.map=map;material.needsUpdate=true;return{mesh,material};
  }));
  const group=new T.Group();group.name='Poster measured right bow v56';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8),positions=new Float32Array(q.vertexCount*3),normals=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
    for(let i=0;i<q.vertexCount;i++){positions.set(packed.subarray(i*8,i*8+3),i*3);normals.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(positions,3));geometry.setAttribute('normal',new T.BufferAttribute(normals,3));geometry.setAttribute('uv',new T.BufferAttribute(uv,2));geometry.computeBoundingBox();geometry.computeBoundingSphere();
    const mesh=new T.Mesh(geometry,q.reuseTargetMaterial?targets.get(q.reuseTargetMaterial).material:paint);mesh.name='Poster right bow '+q.key+' v56';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const ob of targets.values()){ob.parent.remove(ob);ob.geometry.dispose();}scene.add(group);for(const q of surfaceUpdates)q.mesh.material=q.material;
  root.posterRightBowEvidence56={revision:56,closedNewMembers:1,triangles:spec.triangles,depthInferred:true,browserMaterialsApproximate:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
