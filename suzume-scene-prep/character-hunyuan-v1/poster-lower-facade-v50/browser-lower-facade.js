async function applyPosterLowerFacade50(T,scene,root){
  const base='../poster-lower-facade-v50/';
  const responses=await Promise.all(['browser-lower-facade-v50.json','lower-facade-v50.bin'].map(n=>fetch(base+n)));
  if(responses.some(r=>!r.ok))throw Error('Poster lower facade v50 could not be loaded');
  const [spec,buffer]=await Promise.all([responses[0].json(),responses[1].arrayBuffer()]);
  const old=new Map(),originalMaterials=new Map();
  for(const q of spec.buckets.filter(q=>q.materialSource)){
    const mesh=q.previousLocation==='v49'?scene.getObjectByName('Poster arched facade '+q.key+' v49'):q.previousLocation==='v48'?scene.getObjectByName('Poster upper facade '+q.key+' v48'):q.previousLocation==='v46'?scene.getObjectByName('Poster facade '+q.key+' v46'):scene.children.find(o=>o.isMesh&&o.name==='Circular ruined hotel with exterior entrance solid mesh'&&o.geometry.attributes.position.count===q.originalVertexCount);
    if(!mesh||!mesh.isMesh)throw Error('Previous facade does not match v50: '+q.key);old.set(q.key,mesh);originalMaterials.set(q.key,mesh.material);
  }
  const materials=[0,1,2].map(i=>{const mesh=scene.getObjectByName('Poster upper facade new'+i+' v48');if(!mesh)throw Error('Missing v48 facade material '+i);return mesh.material;});
  const group=new T.Group();group.name='Poster observed lower facade v50';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8),p=new Float32Array(q.vertexCount*3),n=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
    for(let i=0;i<q.vertexCount;i++){p.set(packed.subarray(i*8,i*8+3),i*3);n.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
    const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(p,3));geo.setAttribute('normal',new T.BufferAttribute(n,3));geo.setAttribute('uv',new T.BufferAttribute(uv,2));geo.computeBoundingBox();geo.computeBoundingSphere();const mesh=new T.Mesh(geo,q.materialSource?originalMaterials.get(q.materialSource):materials[q.reuseUpperMaterialIndex]);mesh.name='Poster lower facade '+q.key+' v50';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const mesh of old.values()){mesh.parent.remove(mesh);mesh.geometry.dispose();}scene.add(group);
  root.posterLowerFacadeEvidence50={revision:50,closedSolids:spec.closedSolids,openingUnits:spec.openingUnits,triangles:spec.triangles,actualRecessedOpenings:true,browserRuntimeVerified:false,hiddenConstructionInferred:true,oneToOneComplete:false};
}