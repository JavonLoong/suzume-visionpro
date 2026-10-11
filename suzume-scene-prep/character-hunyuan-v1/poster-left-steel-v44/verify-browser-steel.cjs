const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js')),spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-steel-v44.json'))),raw=fs.readFileSync(path.join(__dirname,'steel-v44.bin'));
const scene=new T.Scene(),materials=new Map(),old=[],untouched=new T.Mesh(new T.SphereGeometry(1),new T.MeshBasicMaterial());scene.add(untouched);let disposed=0;
for(const q of spec.buckets.filter(q=>q.originalVertexCount)){
 const material=new T.MeshStandardMaterial();materials.set(q.originalVertexCount,material);const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(q.originalVertexCount*3),3));g.addEventListener('dispose',()=>disposed++);const mesh=new T.Mesh(g,material);mesh.name='Broken radial dome steelwork solid mesh';scene.add(mesh);old.push(mesh);
}
const requested=[];const sandbox={Promise,Map,Error,Float32Array,fetch:async url=>{requested.push(url);const file=path.resolve(root,'viewer',url);assert(file.startsWith(__dirname+path.sep));const b=fs.readFileSync(file);return{ok:true,json:async()=>JSON.parse(b.toString()),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-steel.js'),'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterSteel44(T,scene,evidence);assert.equal(disposed,4);for(const mesh of old)assert.strictEqual(mesh.parent,null);assert.strictEqual(untouched.parent,scene);assert.equal(scene.children.length,2);const group=scene.getObjectByName('Reference-observed poster steel v44');assert.equal(group.children.length,spec.buckets.length);let triangles=0;
 for(const q of spec.buckets){
  const mesh=group.getObjectByName('Poster steel '+q.key+' v44');assert(mesh.castShadow&&mesh.receiveShadow);assert(mesh.matrix.equals(new T.Matrix4()));
  for(const [name,offset,width] of [['position',0,3],['normal',3,3],['uv',6,2]]){
   const data=mesh.geometry.attributes[name].array;assert.equal(data.length,q.vertexCount*width);for(let i=0;i<q.vertexCount;i++)for(let j=0;j<width;j++)assert.equal(data[i*width+j],raw.readFloatLE(q.byteOffset+(i*8+offset+j)*4));
  }
  if(q.originalVertexCount)assert.strictEqual(mesh.material,materials.get(q.originalVertexCount));
  else{const material=spec.newMaterials.find(m=>m.key===q.newMaterialKey);assert.deepStrictEqual(mesh.material.color.toArray(),material.linearRGB);assert.equal(mesh.material.roughness,material.roughness);assert.equal(mesh.material.metalness,material.metalness);}
  triangles+=q.vertexCount/3;
 }
 assert.equal(triangles,spec.triangles);const html=fs.readFileSync(path.join(root,'viewer/poster-v44.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(m[2].trim()){new vm.Script(m[2]);scripts++;}
 assert(html.includes('await applyPosterSteel44(T,scene,root)'));assert(!html.includes('await applyPosterSteel39(T,scene,root)'));assert(html.includes('await applyPosterLowerClouds43(T,scene,root,cloudGeometries)'));assert(html.includes('suzume-poster-view-v44'));assert(requested.every(url=>url.includes('poster-left-steel-v44/')));
 const report={revision:44,nativeSha256:spec.nativeSha256,threeRevision:T.REVISION,inlineScriptsParsed:scripts,triangles,buckets:spec.buckets.length,positionsNormalsUVsMatchNativeExportExactly:true,originalMaterialsReused:true,approximateNewMaterialsMatchSpec:true,unrelatedSceneObjectsPreserved:true,onlyCurrentSteelPayloadRequested:true,browserRuntimeVerified:false,browserMaterialsApproximate:true,scope:'Actual Three.js geometry construction and JavaScript parsing in Node. No browser or GPU execution.'};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v44.json'),JSON.stringify(report,null,2));console.log('LEFT_STEEL_44_BROWSER_DATA_VERIFIED',triangles);
})().catch(error=>{console.error(error);process.exitCode=1;});
