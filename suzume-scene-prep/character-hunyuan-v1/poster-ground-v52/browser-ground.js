async function applyPosterGround52(T,scene,root){
  const base='../poster-ground-v52/',responses=await Promise.all(['browser-ground-v52.json','ground-v52.bin'].map(n=>fetch(base+n)));
  if(responses.some(r=>!r.ok))throw Error('Poster ground v52 could not be loaded');
  const [spec,buffer]=await Promise.all([responses[0].json(),responses[1].arrayBuffer()]),old=new Map(),materials=new Map();
  for(const q of spec.targets){const mesh=q.name?scene.getObjectByName(q.name):scene.children.find(o=>o.isMesh&&o.name===q.originalName&&o.geometry.attributes.position.count===q.originalVertexCount);if(!mesh||!mesh.isMesh)throw Error('Ground baseline does not match v52: '+q.key);old.set(q.key,mesh);materials.set(q.key,mesh.material);}
  const groundMaterials=[.97,.91].map((roughness,i)=>{const m=new T.MeshStandardMaterial({color:0xffffff,vertexColors:true,roughness,metalness:0});m.name=i?'Poster broken stone pigments v52':'Poster wet ground pigments v52';return m;});
  const group=new T.Group();group.name='Poster shallow bank and stones v52';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*12),p=new Float32Array(q.vertexCount*3),n=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2),c=new Float32Array(q.vertexCount*3);
    for(let i=0;i<q.vertexCount;i++){p.set(packed.subarray(i*12,i*12+3),i*3);n.set(packed.subarray(i*12+3,i*12+6),i*3);uv.set(packed.subarray(i*12+6,i*12+8),i*2);c.set(packed.subarray(i*12+8,i*12+11),i*3);}
    const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(p,3));geo.setAttribute('normal',new T.BufferAttribute(n,3));geo.setAttribute('uv',new T.BufferAttribute(uv,2));geo.setAttribute('color',new T.BufferAttribute(c,3));geo.computeBoundingBox();geo.computeBoundingSphere();const mesh=new T.Mesh(geo,q.reuseTargetMaterial?materials.get(q.reuseTargetMaterial):groundMaterials[q.groundMaterialIndex]);mesh.name='Poster ground '+q.key+' v52';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const mesh of old.values()){mesh.parent.remove(mesh);mesh.geometry.dispose();}scene.add(group);
  root.posterGroundEvidence52={revision:52,closedSolids:spec.closedSolids,triangles:spec.triangles,volumetricShallowBank:true,hiddenDepthInferred:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
