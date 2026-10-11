async function applyPosterSteel39(T,scene,root){
  const specResponse=await fetch('../poster-steel-v39/browser-steel-v39.json');
  if(!specResponse.ok)throw Error('Steel geometry metadata unavailable');
  const spec=await specResponse.json();
  const response=await fetch('../poster-steel-v39/steel-v39.bin');
  if(!response.ok)throw Error('Steel geometry unavailable');
  const buffer=await response.arrayBuffer();
  const old=scene.children.filter(o=>o.isMesh&&o.name==='Broken radial dome steelwork solid mesh');
  const originalMaterials=new Map(old.map(o=>[o.geometry.attributes.position.count,o.material]));
  for(const q of spec.buckets)if(q.originalVertexCount&&!originalMaterials.has(q.originalVertexCount))throw Error('Poster steel source does not match the calibrated model');
  const colors=spec.newMaterials.map(m=>new T.MeshStandardMaterial({color:new T.Color().setRGB(...m.linearRGB),roughness:m.roughness,metalness:m.metalness}));
  const group=new T.Group();group.name='Reference-observed poster steel v39';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8);const positions=new Float32Array(q.vertexCount*3),normals=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
    for(let i=0;i<q.vertexCount;i++){positions.set(packed.subarray(i*8,i*8+3),i*3);normals.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(positions,3));geometry.setAttribute('normal',new T.BufferAttribute(normals,3));geometry.setAttribute('uv',new T.BufferAttribute(uv,2));
    const material=q.originalVertexCount?originalMaterials.get(q.originalVertexCount):colors[q.newMaterialIndex];const mesh=new T.Mesh(geometry,material);mesh.name='Poster steel '+q.key+' v39';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  old.forEach(o=>{scene.remove(o);o.geometry.dispose();});scene.add(group);
  root.posterSteelEvidence39={revision:39,closedMembers:16,referenceDepthInferred:true,browserMaterialApproximation:true};
}
