async function applyPosterRailings46(T,scene,root){
  const responses=await Promise.all(['browser-railings-v46.json','facade-railings-v46.bin','ivy-scale-v46.json'].map(name=>fetch('../poster-railings-v46/'+name)));
  if(responses.some(r=>!r.ok))throw Error('Poster railing v46 could not be loaded');
  const [spec,buffer,ivySpec]=await Promise.all([responses[0].json(),responses[1].arrayBuffer(),responses[2].json()]);
  const counts=new Set(spec.buckets.filter(q=>q.originalVertexCount).map(q=>q.originalVertexCount));
  const old=scene.children.filter(o=>o.isMesh&&o.name==='Circular ruined hotel with exterior entrance solid mesh'&&counts.has(o.geometry.attributes.position.count));
  const originalMaterials=new Map(old.map(o=>[o.geometry.attributes.position.count,o.material]));
  if(old.length!==counts.size||originalMaterials.size!==counts.size)throw Error('Original facade does not match v46');
  const ivy=scene.getObjectByName('Individual three-dimensional ivy leaves');
  if(!ivy||!ivy.isInstancedMesh||ivy.count!==ivySpec.sourceInstanceCount)throw Error('Original ivy does not match v46');
  const matrix=new T.Matrix4();
  for(const q of ivySpec.edits){ivy.getMatrixAt(q.index,matrix);for(let j=0;j<16;j++)if(Math.abs(matrix.elements[j]-q.beforeColumnMajorThree[j])>2e-5)throw Error('Original ivy transform does not match v46');}
  const newMaterials=new Map(spec.newMaterials.map(m=>[m.key,new T.MeshStandardMaterial({color:new T.Color().setRGB(...m.linearRGB),roughness:m.roughness,metalness:m.metalness})]));
  const group=new T.Group();group.name='Reference-observed poster facade and rails v46';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8),positions=new Float32Array(q.vertexCount*3),normals=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
    for(let i=0;i<q.vertexCount;i++){positions.set(packed.subarray(i*8,i*8+3),i*3);normals.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(positions,3));geometry.setAttribute('normal',new T.BufferAttribute(normals,3));geometry.setAttribute('uv',new T.BufferAttribute(uv,2));geometry.computeBoundingBox();geometry.computeBoundingSphere();
    const mesh=new T.Mesh(geometry,q.originalVertexCount?originalMaterials.get(q.originalVertexCount):newMaterials.get(q.newMaterialKey));mesh.name='Poster facade '+q.key+' v46';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const ob of old){scene.remove(ob);ob.geometry.dispose();}scene.add(group);
  for(const q of ivySpec.edits){matrix.fromArray(q.afterColumnMajorThree);ivy.setMatrixAt(q.index,matrix);}ivy.instanceMatrix.needsUpdate=true;
  root.posterRailingsEvidence46={revision:46,closedRailAssemblies:4,closedRoofAssemblies:4,triangles:spec.triangles,resizedLeftRoofLeaves:ivySpec.edits.length,browserMaterialsApproximate:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
