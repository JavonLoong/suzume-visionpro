const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js')),spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-railings-v46.json'))),raw=fs.readFileSync(path.join(__dirname,'facade-railings-v46.bin'));
const source=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-source-audit-v46.json'))),ivySpec=JSON.parse(fs.readFileSync(path.join(__dirname,'ivy-scale-v46.json'))),scene=new T.Scene(),materials=new Map(),old=[],untouched=[];let disposed=0;
const counts=new Set(spec.buckets.filter(q=>q.originalVertexCount).map(q=>q.originalVertexCount));
for(const count of source.hotelVertexCounts){
 const material=new T.MeshStandardMaterial();materials.set(count,material);const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(count*3),3));const mesh=new T.Mesh(g,material);mesh.name='Circular ruined hotel with exterior entrance solid mesh';scene.add(mesh);
 if(counts.has(count)){old.push(mesh);g.addEventListener('dispose',()=>disposed++);}else untouched.push(mesh);
}
const steel=new T.Group();steel.name='Reference-observed poster steel v44';scene.add(steel);untouched.push(steel);
const ivy=new T.InstancedMesh(new T.PlaneGeometry(.15,.18),new T.MeshStandardMaterial(),source.ivyCount);ivy.name='Individual three-dimensional ivy leaves';scene.add(ivy);
const ivyBytes=fs.readFileSync(path.join(__dirname,'original-ivy-matrices-v46.bin')),colorBytes=fs.readFileSync(path.join(__dirname,'original-ivy-colors-v46.bin'));
const originalMatrices=new Float32Array(ivyBytes.buffer.slice(ivyBytes.byteOffset,ivyBytes.byteOffset+ivyBytes.byteLength)),colors=new Float32Array(colorBytes.buffer.slice(colorBytes.byteOffset,colorBytes.byteOffset+colorBytes.byteLength));ivy.instanceMatrix.array.set(originalMatrices);ivy.instanceColor=new T.InstancedBufferAttribute(colors,3);const colorIdentity=ivy.instanceColor,originalColors=colors.slice();
const requested=[];const sandbox={Promise,Map,Set,Error,Float32Array,Math,fetch:async url=>{requested.push(url);const file=path.resolve(root,'viewer',url);assert(file.startsWith(__dirname+path.sep));const b=fs.readFileSync(file);return{ok:true,json:async()=>JSON.parse(b.toString()),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-railings.js'),'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterRailings46(T,scene,evidence);assert.equal(disposed,counts.size);for(const mesh of old)assert.strictEqual(mesh.parent,null);for(const mesh of untouched)assert.strictEqual(mesh.parent,scene);const group=scene.getObjectByName('Reference-observed poster facade and rails v46');assert.equal(group.children.length,spec.buckets.length);let triangles=0;
 for(const q of spec.buckets){
  const mesh=group.getObjectByName('Poster facade '+q.key+' v46');assert(mesh.castShadow&&mesh.receiveShadow);assert(mesh.matrix.equals(new T.Matrix4()));
  for(const [name,offset,width] of [['position',0,3],['normal',3,3],['uv',6,2]]){
   const data=mesh.geometry.attributes[name].array;assert.equal(data.length,q.vertexCount*width);for(let i=0;i<q.vertexCount;i++)for(let j=0;j<width;j++)assert.equal(data[i*width+j],raw.readFloatLE(q.byteOffset+(i*8+offset+j)*4));
  }
  if(q.originalVertexCount)assert.strictEqual(mesh.material,materials.get(q.originalVertexCount));
  else{const material=spec.newMaterials.find(m=>m.key===q.newMaterialKey);assert.deepStrictEqual(mesh.material.color.toArray(),material.linearRGB);assert.equal(mesh.material.roughness,material.roughness);assert.equal(mesh.material.metalness,material.metalness);}
  triangles+=q.vertexCount/3;
 }
 const edits=new Map(ivySpec.edits.map(q=>[q.index,q]));
 for(let i=0;i<ivy.count;i++)for(let j=0;j<16;j++)assert.equal(ivy.instanceMatrix.array[i*16+j],edits.has(i)?Math.fround(edits.get(i).afterColumnMajorThree[j]):originalMatrices[i*16+j]);
 assert.strictEqual(ivy.instanceColor,colorIdentity);assert.deepStrictEqual(ivy.instanceColor.array,originalColors);assert.strictEqual(ivy.parent,scene);
 assert.equal(triangles,spec.triangles);const html=fs.readFileSync(path.join(root,'viewer/poster-v46.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(m[2].trim()){new vm.Script(m[2]);scripts++;}
 assert(html.includes('await applyPosterRailings46(T,scene,root)'));assert(!html.includes('await applyPosterRooftops45(T,scene,root)'));assert(html.includes('await applyPosterSteel44(T,scene,root)'));assert(html.includes('await applyPosterLowerClouds43(T,scene,root,cloudGeometries)'));assert(html.includes('suzume-poster-view-v46'));assert(requested.every(url=>url.includes('poster-railings-v46/')));
 const report={revision:46,nativeSha256:spec.nativeSha256,threeRevision:T.REVISION,inlineScriptsParsed:scripts,triangles,buckets:spec.buckets.length,originalFacadeBucketsReplaced:old.length,otherFacadeAndSteelObjectsPreserved:untouched.length,positionsNormalsUVsMatchNativeExportExactly:true,originalMaterialsReused:true,approximateNewMaterialsMatchSpec:true,unrelatedSceneObjectsPreserved:true,ivySourceMatchesOriginalSceneExport:true,ivyChangedMatricesMatchNative:edits.size,otherIvyMatricesAndAllColorsPreservedExactly:true,browserRuntimeVerified:false,browserMaterialsApproximate:true,scope:'Actual Three.js geometry construction, original saved scene instance matrices, and JavaScript parsing in Node. No browser or GPU execution.'};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v46.json'),JSON.stringify(report,null,2));console.log('RAIL_46_BROWSER_DATA_VERIFIED',triangles,'IVY',edits.size);
})().catch(error=>{console.error(error);process.exitCode=1;});
