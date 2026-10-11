async function applyPosterLowRails53(T,scene,root){
  const base='../poster-low-rails-v53/',responses=await Promise.all(['browser-low-rails-v53.json','low-rails-v53.bin'].map(n=>fetch(base+n)));
  if(responses.some(r=>!r.ok))throw Error('Poster low fixtures v53 could not be loaded');
  const [spec,buffer]=await Promise.all([responses[0].json(),responses[1].arrayBuffer()]),old=new Map(),materials=new Map();
  for(const q of spec.targets){const mesh=scene.children.find(o=>o.isMesh&&o.name===q.originalName&&o.geometry.attributes.position.count===q.originalVertexCount);if(!mesh)throw Error('Low fixture baseline does not match v53: '+q.key);old.set(q.key,mesh);materials.set(q.key,mesh.material);}
  const fixtureMaterials=[['Poster faded low frame paint v53',.85,.07],['Poster corroded low frame metal v53',.94,.12],['Poster damaged low frame boards v53',.97,0]].map(([name,roughness,metalness])=>{const m=new T.MeshStandardMaterial({color:0xffffff,vertexColors:true,roughness,metalness});m.name=name;return m;});
  const group=new T.Group();group.name='Poster low frame and pipe supports v53';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*12),p=new Float32Array(q.vertexCount*3),n=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2),c=new Float32Array(q.vertexCount*3);
    for(let i=0;i<q.vertexCount;i++){p.set(packed.subarray(i*12,i*12+3),i*3);n.set(packed.subarray(i*12+3,i*12+6),i*3);uv.set(packed.subarray(i*12+6,i*12+8),i*2);c.set(packed.subarray(i*12+8,i*12+11),i*3);}
    const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(p,3));geo.setAttribute('normal',new T.BufferAttribute(n,3));geo.setAttribute('uv',new T.BufferAttribute(uv,2));geo.setAttribute('color',new T.BufferAttribute(c,3));geo.computeBoundingBox();geo.computeBoundingSphere();const mesh=new T.Mesh(geo,q.reuseTargetMaterial?materials.get(q.reuseTargetMaterial):fixtureMaterials[q.fixtureMaterialIndex]);mesh.name='Poster low fixture '+q.key+' v53';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const mesh of old.values()){mesh.parent.remove(mesh);mesh.geometry.dispose();}scene.add(group);
  root.posterLowFixturesEvidence53={revision:53,closedSolids:spec.closedSolids,triangles:spec.triangles,groundSupportsVerified:true,hiddenDepthInferred:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
