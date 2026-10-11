async function applyPosterRooftops45(T,scene,root){
  const [metaResponse,binResponse]=await Promise.all([fetch('../poster-rooftops-v45/browser-rooftops-v45.json'),fetch('../poster-rooftops-v45/rooftops-v45.bin')]);
  if(!metaResponse.ok||!binResponse.ok)throw Error('Poster rooftop v45 could not be loaded');
  const spec=await metaResponse.json(),buffer=await binResponse.arrayBuffer();
  const counts=new Set(spec.buckets.filter(q=>q.originalVertexCount).map(q=>q.originalVertexCount));
  const old=scene.children.filter(o=>o.isMesh&&o.name==='Circular ruined hotel with exterior entrance solid mesh'&&counts.has(o.geometry.attributes.position.count));
  const originalMaterials=new Map(old.map(o=>[o.geometry.attributes.position.count,o.material]));
  if(old.length!==counts.size||originalMaterials.size!==counts.size)throw Error('Original facade does not match v45');
  const newMaterials=new Map(spec.newMaterials.map(m=>[m.key,new T.MeshStandardMaterial({color:new T.Color().setRGB(...m.linearRGB),roughness:m.roughness,metalness:m.metalness})]));
  const group=new T.Group();group.name='Reference-observed poster rooftops v45';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8),positions=new Float32Array(q.vertexCount*3),normals=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
    for(let i=0;i<q.vertexCount;i++){positions.set(packed.subarray(i*8,i*8+3),i*3);normals.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(positions,3));geometry.setAttribute('normal',new T.BufferAttribute(normals,3));geometry.setAttribute('uv',new T.BufferAttribute(uv,2));geometry.computeBoundingBox();geometry.computeBoundingSphere();
    const mesh=new T.Mesh(geometry,q.originalVertexCount?originalMaterials.get(q.originalVertexCount):newMaterials.get(q.newMaterialKey));mesh.name='Poster rooftop '+q.key+' v45';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const ob of old){scene.remove(ob);ob.geometry.dispose();}scene.add(group);
  root.posterRooftopsEvidence45={revision:45,closedAssemblies:4,triangles:spec.triangles,roofSupportsVerified:true,referenceDepthInferred:true,browserMaterialsApproximate:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
