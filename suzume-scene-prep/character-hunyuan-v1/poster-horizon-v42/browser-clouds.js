// Import the final native cloud set directly, avoiding the superseded v41 payload.
async function applyPosterHorizon42(T,scene,root,cloudGeometries){
  const [metaResponse,binResponse]=await Promise.all([fetch('../poster-horizon-v42/browser-clouds-v42.json'),fetch('../poster-horizon-v42/clouds-v42.bin')]);
  if(!metaResponse.ok||!binResponse.ok)throw Error('Cloud geometry v42 could not be loaded');
  const spec=await metaResponse.json(),bytes=await binResponse.arrayBuffer();
  const oldMeshes=spec.replaces.map(name=>{
    const mesh=scene.getObjectByName(name);
    if(!mesh||!mesh.isMesh||mesh.parent!==scene||!cloudGeometries.includes(mesh.geometry))throw Error('Original poster cloud missing: '+name);
    return mesh;
  });
  const oldByName=new Map(oldMeshes.map(mesh=>[mesh.name,mesh]));
  const rebuilt=spec.clouds.map(q=>{
    const g=new T.BufferGeometry();
    for(const [attribute,key] of [['position','positions'],['normal','normals'],['color','colors']]){
      const segment=q[key];g.setAttribute(attribute,new T.BufferAttribute(new Float32Array(bytes,segment.byteOffset,segment.byteLength/4),3));
    }
    g.setIndex(new T.BufferAttribute(new Uint32Array(bytes,q.indices.byteOffset,q.indices.byteLength/4),1));g.computeBoundingBox();g.computeBoundingSphere();
    const material=(oldByName.get(q.name)||oldByName.get('Distant reference closed cloud 1')).material;
    const mesh=new T.Mesh(g,material);mesh.name=q.name;mesh.matrix.fromArray(q.matrix);mesh.matrix.decompose(mesh.position,mesh.quaternion,mesh.scale);mesh.matrixAutoUpdate=false;
    return mesh;
  });
  const oldGeometries=new Set(oldMeshes.map(mesh=>mesh.geometry));
  const preserved=cloudGeometries.filter(g=>!oldGeometries.has(g));
  for(const mesh of oldMeshes)scene.remove(mesh);
  for(const mesh of rebuilt){scene.add(mesh);mesh.updateMatrixWorld(true);}
  cloudGeometries.splice(0,cloudGeometries.length,...preserved,...rebuilt.map(mesh=>mesh.geometry));
  for(const g of oldGeometries)g.dispose();
  root.posterCloudEvidence42={revision:42,clouds:spec.clouds.length,vertices:spec.vertices,triangles:spec.triangles,restoredContinuousBank:true,closedNativeGeometry:true,unknownDepthInferred:true,noCameraFacingCards:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
