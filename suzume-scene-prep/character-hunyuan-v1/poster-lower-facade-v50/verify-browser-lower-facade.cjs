const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js')),spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-lower-facade-v50.json'))),raw=fs.readFileSync(path.join(__dirname,'lower-facade-v50.bin'));
const B=path.join(root,'poster-railings-v46'),source=JSON.parse(fs.readFileSync(path.join(B,'browser-source-audit-v46.json'))),scene=new T.Scene(),original=[];
for(const count of source.hotelVertexCounts){const geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(new Float32Array(count*3),3));const mat=count===119061?new T.MeshBasicMaterial({toneMapped:false,fog:false}):new T.MeshStandardMaterial();const ob=new T.Mesh(geo,mat);ob.name='Circular ruined hotel with exterior entrance solid mesh';scene.add(ob);original.push(ob);}
const steel=new T.Group();steel.name='Reference-observed poster steel v44';scene.add(steel);
const ivy=new T.InstancedMesh(new T.PlaneGeometry(.15,.18),new T.MeshStandardMaterial(),source.ivyCount);ivy.name='Individual three-dimensional ivy leaves';scene.add(ivy);
const data=fs.readFileSync(path.join(B,'original-ivy-matrices-v46.bin'));ivy.instanceMatrix.array.set(new Float32Array(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength)));
const requested=[];T.TextureLoader=class{load(url,done){requested.push(url);const png=fs.readFileSync(path.resolve(root,'viewer',url));assert.equal(png.toString('hex',0,8),'89504e470d0a1a0a');const tex=new T.Texture();tex.userData={source:url};done(tex);return tex;}};
const sandbox={Promise,Map,Set,Error,Float32Array,Math,fetch:async url=>{requested.push(url);const file=path.resolve(root,'viewer',url);assert(file.startsWith(root+path.sep));const b=fs.readFileSync(file);return{ok:true,json:async()=>JSON.parse(b.toString()),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}};vm.createContext(sandbox);
for(const file of ['poster-railings-v46/browser-railings.js','poster-fascia-v47/browser-fascia.js','poster-upper-windows-v48/browser-upper-windows.js','poster-arches-v49/browser-arches.js','poster-lower-facade-v50/browser-lower-facade.js'])vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterRailings46(T,scene,evidence);await sandbox.applyPosterFascia47(T,scene,evidence);await sandbox.applyPosterUpperWindows48(T,scene,evidence);await sandbox.applyPosterArches49(T,scene,evidence);
 const targets=new Map(),mats=new Map(),upperMats=[0,1,2].map(i=>scene.getObjectByName('Poster upper facade new'+i+' v48').material);let disposed=0;
 for(const q of spec.buckets){
  let ob;
  if(q.materialSource)ob=q.previousLocation==='v49'?scene.getObjectByName('Poster arched facade '+q.key+' v49'):q.previousLocation==='v48'?scene.getObjectByName('Poster upper facade '+q.key+' v48'):q.previousLocation==='v46'?scene.getObjectByName('Poster facade '+q.key+' v46'):scene.children.find(o=>o.isMesh&&o.name==='Circular ruined hotel with exterior entrance solid mesh'&&o.geometry.attributes.position.count===q.originalVertexCount);
  else if(q.replacePreviousNewIndex!==undefined)ob=scene.getObjectByName('Poster upper facade new'+q.replacePreviousNewIndex+' v48');
  else continue;
  assert(ob);targets.set(q.key,ob);mats.set(q.key,ob.material);ob.geometry.addEventListener('dispose',()=>disposed++);
 }
 const untouched=[];scene.traverse(ob=>{if(ob!==scene&&!Array.from(targets.values()).includes(ob))untouched.push([ob,ob.parent,ob.geometry,ob.material,ob.matrix.clone()]);});const ivyBefore=ivy.instanceMatrix.array.slice();
 await sandbox.applyPosterLowerFacade50(T,scene,evidence);assert.equal(disposed,14);for(const ob of targets.values())assert.strictEqual(ob.parent,null);
 for(const [ob,parent,geometry,material,matrix] of untouched){assert.strictEqual(ob.parent,parent);assert.strictEqual(ob.geometry,geometry);assert.strictEqual(ob.material,material);assert(ob.matrix.equals(matrix));}assert.deepStrictEqual(ivy.instanceMatrix.array,ivyBefore);
 const group=scene.getObjectByName('Poster observed lower facade v50');assert.equal(group.children.length,spec.buckets.length);let triangles=0;
 for(const q of spec.buckets){
  const ob=group.getObjectByName('Poster lower facade '+q.key+' v50');assert(ob.castShadow&&ob.receiveShadow);assert(ob.matrix.equals(new T.Matrix4()));
  for(const [name,offset,width] of [['position',0,3],['normal',3,3],['uv',6,2]]){const a=ob.geometry.attributes[name].array;assert.equal(a.length,q.vertexCount*width);for(let i=0;i<q.vertexCount;i++)for(let j=0;j<width;j++)assert.equal(a[i*width+j],raw.readFloatLE(q.byteOffset+(i*8+offset+j)*4));}
  assert.strictEqual(ob.material,q.materialSource?mats.get(q.materialSource):upperMats[q.reuseUpperMaterialIndex]);triangles+=q.vertexCount/3;
 }
 const html=fs.readFileSync(path.join(root,'viewer/poster-v50.html'),'utf8');let scripts=0;for(const q of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(q[2].trim()){new vm.Script(q[2]);scripts++;}
 const calls=['await applyPosterRailings46(T,scene,root);','await applyPosterFascia47(T,scene,root);','await applyPosterUpperWindows48(T,scene,root);','await applyPosterArches49(T,scene,root);','await applyPosterLowerFacade50(T,scene,root);'];for(let i=0;i<calls.length;i++){assert(html.includes(calls[i]));if(i)assert(html.indexOf(calls[i])>html.indexOf(calls[i-1]));}assert(html.includes('suzume-poster-view-v50'));assert.equal(triangles,spec.triangles);
 const report={revision:50,nativeSha256:spec.nativeSha256,threeRevision:T.REVISION,inlineScriptsParsed:scripts,triangles,buckets:spec.buckets.length,previousFacadeBucketsReplaced:14,positionsNormalsUVsMatchNativeExactly:true,previousUnaffectedGeometryMaterialsAndIvyPreserved:true,allMaterialInstancesReused:true,browserRuntimeVerified:false,browserMaterialsApproximate:true,scope:'Actual Three.js construction and chained v46-v50 data loading in Node; PNG bytes checked with a texture-loader shim. No browser/GPU rendering.'};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v50.json'),JSON.stringify(report,null,2));console.log('LOWER_FACADE_50_BROWSER_DATA_VERIFIED',triangles);
})().catch(error=>{console.error(error);process.exitCode=1;});
