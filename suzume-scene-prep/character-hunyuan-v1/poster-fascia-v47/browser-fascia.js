async function applyPosterFascia47(T,scene,root){
  const response=await fetch('../poster-fascia-v47/browser-fascia-v47.json');
  if(!response.ok)throw Error('Poster fascia v47 could not be loaded');
  const spec=await response.json();
  const materials=spec.materials.map(m=>new T.MeshStandardMaterial({color:new T.Color().setRGB(...m.linearRGB),roughness:m.roughness,metalness:m.metalness}));
  const group=new T.Group();group.name='Poster molded roof fascia v47';
  for(const q of spec.members){
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute(q.positions,3));geometry.setAttribute('normal',new T.Float32BufferAttribute(q.normals,3));
    q.materialIndices.forEach((m,i)=>geometry.addGroup(i*3,3,m));geometry.computeBoundingBox();geometry.computeBoundingSphere();
    const mesh=new T.Mesh(geometry,materials);mesh.name=q.name;mesh.castShadow=mesh.receiveShadow=true;group.add(mesh);
  }
  scene.add(group);root.posterFasciaEvidence47={revision:47,closedSolids:spec.members.length,triangles:spec.triangles,nativeSha256:spec.nativeSha256,browserRuntimeVerified:false,browserMaterialsApproximate:true,oneToOneComplete:false};
}
