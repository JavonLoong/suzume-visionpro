async function applyPosterForeground51(T,scene,root){
  const base='../poster-foreground-v51/';
  const responses=await Promise.all(['browser-foreground-v51.json','foreground-v51.bin'].map(n=>fetch(base+n)));
  if(responses.some(r=>!r.ok))throw Error('Poster foreground v51 could not be loaded');
  const [spec,buffer]=await Promise.all([responses[0].json(),responses[1].arrayBuffer()]);
  const old=new Map(),originalMaterials=new Map();
  for(const q of spec.buckets.filter(q=>q.materialSource)){
    const mesh=q.previousLocation==='v50'?scene.getObjectByName('Poster lower facade '+q.key+' v50'):scene.children.find(o=>o.isMesh&&o.name==='Circular ruined hotel with exterior entrance solid mesh'&&o.geometry.attributes.position.count===q.originalVertexCount);
    if(!mesh||!mesh.isMesh)throw Error('Previous foreground does not match v51: '+q.key);old.set(q.key,mesh);originalMaterials.set(q.key,mesh.material);
  }
  const materials=[0,1].map(i=>{const mesh=scene.getObjectByName('Poster upper facade new'+i+' v48');if(!mesh)throw Error('Missing v48 facade material '+i);return mesh.material;});
  const ivy=scene.getObjectByName('Individual three-dimensional ivy leaves');
  if(!ivy||!ivy.isInstancedMesh||ivy.count!==spec.ivyRemoval.sourceCount)throw Error('Unexpected ivy baseline for v51');
  const removed=new Set(spec.ivyRemoval.removedIndices);if(removed.size!==ivy.count-spec.ivyRemoval.remainingCount)throw Error('Invalid ivy removal map');
  const nextIvy=new T.InstancedMesh(ivy.geometry,ivy.material,spec.ivyRemoval.remainingCount);nextIvy.name=ivy.name;nextIvy.position.copy(ivy.position);nextIvy.quaternion.copy(ivy.quaternion);nextIvy.scale.copy(ivy.scale);nextIvy.matrix.copy(ivy.matrix);nextIvy.matrixAutoUpdate=ivy.matrixAutoUpdate;nextIvy.castShadow=ivy.castShadow;nextIvy.receiveShadow=ivy.receiveShadow;nextIvy.visible=ivy.visible;nextIvy.frustumCulled=ivy.frustumCulled;nextIvy.layers.mask=ivy.layers.mask;nextIvy.renderOrder=ivy.renderOrder;nextIvy.userData={...ivy.userData,foregroundRevision:51};
  const matrix=new T.Matrix4(),color=new T.Color();let j=0;
  for(let i=0;i<ivy.count;i++)if(!removed.has(i)){ivy.getMatrixAt(i,matrix);nextIvy.setMatrixAt(j,matrix);if(ivy.instanceColor){ivy.getColorAt(i,color);nextIvy.setColorAt(j,color);}j++;}
  if(j!==nextIvy.count)throw Error('Invalid filtered ivy count');nextIvy.instanceMatrix.needsUpdate=true;if(nextIvy.instanceColor)nextIvy.instanceColor.needsUpdate=true;
  const foliage=new T.MeshStandardMaterial({color:0xffffff,vertexColors:true,roughness:.96,metalness:0});foliage.name='Poster fine foliage pigments v51';
  const group=new T.Group();group.name='Poster foreground plants and props v51';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*12),p=new Float32Array(q.vertexCount*3),n=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2),c=new Float32Array(q.vertexCount*3);
    for(let i=0;i<q.vertexCount;i++){p.set(packed.subarray(i*12,i*12+3),i*3);n.set(packed.subarray(i*12+3,i*12+6),i*3);uv.set(packed.subarray(i*12+6,i*12+8),i*2);c.set(packed.subarray(i*12+8,i*12+11),i*3);}
    const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(p,3));geo.setAttribute('normal',new T.BufferAttribute(n,3));geo.setAttribute('uv',new T.BufferAttribute(uv,2));geo.setAttribute('color',new T.BufferAttribute(c,3));geo.computeBoundingBox();geo.computeBoundingSphere();const mesh=new T.Mesh(geo,q.materialSource?originalMaterials.get(q.materialSource):q.newFoliageMaterial?foliage:materials[q.reuseUpperMaterialIndex]);mesh.name='Poster foreground '+q.key+' v51';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const mesh of old.values()){mesh.parent.remove(mesh);mesh.geometry.dispose();}
  const parent=ivy.parent;parent.remove(ivy);parent.add(nextIvy);scene.add(group);
  root.posterForegroundEvidence51={revision:51,closedSolids:spec.closedSolids,newLeaves:spec.newLeafCount,triangles:spec.triangles,removedLargeLeaves:removed.size,remainingOriginalLeaves:nextIvy.count,browserRuntimeVerified:false,hiddenConstructionInferred:true,oneToOneComplete:false};
}
