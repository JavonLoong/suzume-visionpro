// Dense closed cloud geometry exported from the freshly reopened native scene.
async function applyPosterClouds41(T,scene,root,cloudGeometries){
  const [metaResponse,binResponse]=await Promise.all([fetch('../poster-clouds-v41/browser-clouds-v41.json'),fetch('../poster-clouds-v41/clouds-v41.bin')]);
  if(!metaResponse.ok||!binResponse.ok)throw Error('Cloud geometry v41 could not be loaded');
  const spec=await metaResponse.json(),bytes=await binResponse.arrayBuffer();let vertices=0,triangles=0;
  for(const q of spec.clouds){
    const mesh=scene.getObjectByName(q.name);if(!mesh||!mesh.isMesh||mesh.parent!==scene)throw Error('Poster cloud missing: '+q.name);
    const old=mesh.geometry,slot=cloudGeometries.indexOf(old);if(slot<0)throw Error('Cloud inspection geometry missing: '+q.name);
    const g=new T.BufferGeometry();
    for(const [attribute,key] of [['position','positions'],['normal','normals'],['color','colors']]){
      const segment=q[key];g.setAttribute(attribute,new T.BufferAttribute(new Float32Array(bytes,segment.byteOffset,segment.byteLength/4),3));
    }
    g.setIndex(new T.BufferAttribute(new Uint32Array(bytes,q.indices.byteOffset,q.indices.byteLength/4),1));g.computeBoundingBox();g.computeBoundingSphere();
    mesh.geometry=g;mesh.matrix.fromArray(q.matrix);mesh.matrix.decompose(mesh.position,mesh.quaternion,mesh.scale);mesh.matrixAutoUpdate=false;mesh.updateMatrixWorld(true);cloudGeometries[slot]=g;old.dispose();vertices+=q.vertices;triangles+=q.triangles;
  }
  root.posterCloudEvidence41={revision:41,clouds:spec.clouds.length,vertices,triangles,closedNativeGeometry:true,unknownDepthInferred:true,noCameraFacingCards:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
