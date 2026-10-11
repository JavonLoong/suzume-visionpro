async function applyPosterUpperWindows48(T,scene,root){
  const base='../poster-upper-windows-v48/';
  const responses=await Promise.all(['browser-upper-windows-v48.json','upper-facade-v48.bin'].map(n=>fetch(base+n)));
  if(responses.some(r=>!r.ok))throw Error('Poster upper windows v48 could not be loaded');
  const [spec,buffer]=await Promise.all([responses[0].json(),responses[1].arrayBuffer()]);
  const old=new Map(),originalMaterials=new Map();
  for(const q of spec.buckets.filter(q=>q.materialSource)){
    const mesh=q.previousLocation==='v46'?scene.getObjectByName('Poster facade '+q.key+' v46'):scene.children.find(o=>o.isMesh&&o.name==='Circular ruined hotel with exterior entrance solid mesh'&&o.geometry.attributes.position.count===q.originalVertexCount);
    if(!mesh||!mesh.isMesh)throw Error('Previous facade does not match v48: '+q.key);old.set(q.key,mesh);originalMaterials.set(q.key,mesh.material);
  }
  const textures=new Map(await Promise.all([spec.atlasFile,spec.cleanAtlasFile].map(async file=>{const texture=await new Promise((resolve,reject)=>new T.TextureLoader().load(base+file,resolve,undefined,reject));texture.encoding=T.sRGBEncoding;texture.anisotropy=8;return [file,texture];})));
  const materials=spec.newMaterials.map(m=>{
    if(m.kind==='reuse')return originalMaterials.get(m.source);
    if(m.kind==='clonePaint'){const mat=originalMaterials.get(m.source).clone();mat.map=textures.get(m.textureFile);mat.needsUpdate=true;return mat;}
    return new T.MeshStandardMaterial({color:new T.Color().setRGB(...m.linearRGB),roughness:m.roughness,metalness:m.metalness});
  });
  const group=new T.Group();group.name='Poster corrected upper window storey v48';
  for(const q of spec.buckets){
    const packed=new Float32Array(buffer,q.byteOffset,q.vertexCount*8),p=new Float32Array(q.vertexCount*3),n=new Float32Array(q.vertexCount*3),uv=new Float32Array(q.vertexCount*2);
    for(let i=0;i<q.vertexCount;i++){p.set(packed.subarray(i*8,i*8+3),i*3);n.set(packed.subarray(i*8+3,i*8+6),i*3);uv.set(packed.subarray(i*8+6,i*8+8),i*2);}
    const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(p,3));geo.setAttribute('normal',new T.BufferAttribute(n,3));geo.setAttribute('uv',new T.BufferAttribute(uv,2));geo.computeBoundingBox();geo.computeBoundingSphere();const material=q.materialOverrideNewIndex!==undefined?materials[q.materialOverrideNewIndex]:q.materialSource?originalMaterials.get(q.materialSource):materials[q.newMaterialIndex];const mesh=new T.Mesh(geo,material);mesh.name='Poster upper facade '+q.key+' v48';mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  for(const mesh of old.values()){mesh.parent.remove(mesh);mesh.geometry.dispose();}scene.add(group);
  root.posterUpperWindowsEvidence48={revision:48,closedSolids:spec.closedSolids,triangles:spec.triangles,actualWallOpenings:true,browserRuntimeVerified:false,viewDependentGlazingApproximate:true,oneToOneComplete:false};
}
