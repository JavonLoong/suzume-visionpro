async function applyPosterRightArches55(T,scene,root){
 const base='../poster-right-arches-v55/',responses=await Promise.all(['browser-right-arches-v55.json','right-arches-v55.bin'].map(n=>fetch(base+n)));
 if(responses.some(r=>!r.ok))throw Error('Poster right arcade v55 could not be loaded');
 const [spec,buffer]=await Promise.all([responses[0].json(),responses[1].arrayBuffer()]),old=new Map(),materials=new Map();
 for(const q of spec.targets){const mesh=q.name?scene.getObjectByName(q.name):scene.children.find(o=>o.isMesh&&o.name===q.originalName&&o.geometry.attributes.position.count===q.originalVertexCount);if(!mesh||!mesh.isMesh)throw Error('Right arcade baseline does not match v55: '+q.key);old.set(q.key,mesh);materials.set(q.key,mesh.material);}
 const newMaterials=[materials.get('prior54_0').clone(),materials.get('prior54_1'),materials.get('prior54_2')];const texture=await new Promise((resolve,reject)=>new T.TextureLoader().load(base+spec.atlasFile,resolve,undefined,reject));texture.encoding=T.sRGBEncoding;texture.anisotropy=8;newMaterials[0].name='Poster calibrated right arcade pigments v55';newMaterials[0].map=texture;newMaterials[0].needsUpdate=true;const group=new T.Group();group.name='Poster calibrated right arcade v55';
 for(const q of spec.buckets){
  const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8),p=new Float32Array(q.vertexCount*3),n=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
  for(let i=0;i<q.vertexCount;i++){p.set(packed.subarray(i*8,i*8+3),i*3);n.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
  const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(p,3));geo.setAttribute('normal',new T.BufferAttribute(n,3));geo.setAttribute('uv',new T.BufferAttribute(uv,2));geo.computeBoundingBox();geo.computeBoundingSphere();const mesh=new T.Mesh(geo,q.reuseTargetMaterial?materials.get(q.reuseTargetMaterial):newMaterials[q.newMaterialIndex]);mesh.name='Poster right arcade '+q.key+' v55';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
 }
 for(const mesh of old.values()){mesh.parent.remove(mesh);mesh.geometry.dispose();}scene.add(group);root.posterRightArcadeEvidence55={revision:55,closedSolids:spec.closedSolids,archUnits:spec.archUnits,triangles:spec.triangles,curvedVolumetricWall:true,hiddenDepthInferred:true,browserRuntimeVerified:false,oneToOneComplete:false};
}
