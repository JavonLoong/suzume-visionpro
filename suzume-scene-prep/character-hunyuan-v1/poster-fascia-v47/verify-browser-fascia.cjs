const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js')),spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-fascia-v47.json')));
const scene=new T.Scene(),prior=new T.Group();prior.name='Reference-observed poster facade and rails v46';scene.add(prior);
const originalMatrix=new T.Matrix4().makeTranslation(2,3,4),mesh=new T.Mesh(new T.BoxGeometry(),new T.MeshStandardMaterial());mesh.applyMatrix4(originalMatrix);prior.add(mesh);
const ivy=new T.InstancedMesh(new T.PlaneGeometry(),new T.MeshStandardMaterial(),4443);ivy.name='Individual three-dimensional ivy leaves';scene.add(ivy);const ivyBefore=ivy.instanceMatrix.array.slice();
const oldChildren=scene.children.slice(),g=mesh.geometry,m=mesh.material;
const sandbox={Promise,Error,fetch:async url=>{assert.equal(url,'../poster-fascia-v47/browser-fascia-v47.json');return{ok:true,json:async()=>spec};}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-fascia.js'),'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterFascia47(T,scene,evidence);const group=scene.getObjectByName('Poster molded roof fascia v47');assert.equal(group.children.length,4);
 let triangles=0;
 for(const q of spec.members){
  const ob=group.getObjectByName(q.name);assert(ob&&ob.castShadow&&ob.receiveShadow);assert(ob.matrix.equals(new T.Matrix4()));
  assert.deepStrictEqual(Array.from(ob.geometry.attributes.position.array),q.positions);assert.deepStrictEqual(Array.from(ob.geometry.attributes.normal.array),q.normals);
  for(let i=0;i<q.materialIndices.length;i++)assert.deepStrictEqual(ob.geometry.groups[i],{start:i*3,count:3,materialIndex:q.materialIndices[i]});
  spec.materials.forEach((q,i)=>{assert.deepStrictEqual(ob.material[i].color.toArray(),q.linearRGB);assert.equal(ob.material[i].roughness,q.roughness);assert.equal(ob.material[i].metalness,q.metalness);});
  triangles+=q.positions.length/9;
 }
 oldChildren.forEach(ob=>assert.strictEqual(ob.parent,scene));assert.strictEqual(mesh.geometry,g);assert.strictEqual(mesh.material,m);assert(mesh.matrix.equals(originalMatrix));assert.deepStrictEqual(ivy.instanceMatrix.array,ivyBefore);
 const html=fs.readFileSync(path.join(root,'viewer/poster-v47.html'),'utf8');let scripts=0;for(const q of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(q[2].trim()){new vm.Script(q[2]);scripts++;}
 for(const text of ['await applyPosterRailings46(T,scene,root);','await applyPosterFascia47(T,scene,root);','await applyPosterSteel44(T,scene,root);','await applyPosterLowerClouds43(T,scene,root,cloudGeometries);','suzume-poster-view-v47'])assert(html.includes(text));
 assert(html.indexOf('await applyPosterRailings46(T,scene,root);')<html.indexOf('await applyPosterFascia47(T,scene,root);'));assert.equal(triangles,128);
 const report={revision:47,nativeSha256:spec.nativeSha256,threeRevision:T.REVISION,inlineScriptsParsed:scripts,triangles,closedSolids:4,positionsNormalsMaterialAssignmentsMatchNativeExactly:true,previousSceneAndIvyPreserved:true,newMaterialParametersMatchNativeSpec:true,browserRuntimeVerified:false,browserMaterialsApproximate:true,scope:'Actual Three.js mesh construction and source parsing in Node. Browser GPU execution is still unverified.'};
 fs.writeFileSync(path.join(__dirname,'browser-code-verification-v47.json'),JSON.stringify(report,null,2));console.log('FASCIA_47_BROWSER_DATA_VERIFIED',triangles);
})().catch(error=>{console.error(error);process.exitCode=1;});
