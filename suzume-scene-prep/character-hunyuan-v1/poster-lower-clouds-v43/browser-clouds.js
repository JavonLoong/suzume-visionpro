async function applyPosterLowerClouds43(T,scene,root,cloudGeometries){
  const [metaResponse,binResponse]=await Promise.all([fetch('../poster-lower-clouds-v43/browser-clouds-v43.json'),fetch('../poster-lower-clouds-v43/lower-clouds-v43.bin')]);
  if(!metaResponse.ok||!binResponse.ok)throw Error('Lower cloud geometry v43 could not be loaded');
  const spec=await metaResponse.json(),bytes=await binResponse.arrayBuffer();
  const reference=scene.getObjectByName('Restored central horizon cloud bank v42');if(!reference)throw Error('The preceding cloud bank is missing');
  for(const q of spec.clouds){
    if(scene.getObjectByName(q.name))throw Error('Duplicate lower cloud '+q.name);
    const g=new T.BufferGeometry();
    for(const [attribute,key] of [['position','positions'],['normal','normals'],['color','colors']]){const part=q[key];g.setAttribute(attribute,new T.BufferAttribute(new Float32Array(bytes,part.byteOffset,part.byteLength/4),3));}
    g.setIndex(new T.BufferAttribute(new Uint32Array(bytes,q.indices.byteOffset,q.indices.byteLength/4),1));g.computeBoundingBox();g.computeBoundingSphere();
    const mesh=new T.Mesh(g,reference.material);mesh.name=q.name;mesh.matrix.fromArray(q.matrix);mesh.matrix.decompose(mesh.position,mesh.quaternion,mesh.scale);mesh.matrixAutoUpdate=false;scene.add(mesh);mesh.updateMatrixWorld(true);cloudGeometries.push(g);
  }
  root.posterLowerCloudEvidence43={revision:43,clouds:spec.clouds.length,triangles:spec.triangles,closedNativeGeometry:true,unknownDepthInferred:true,noCameraFacingCards:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
