const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js'));
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-clouds-v43.json'))),previous=JSON.parse(fs.readFileSync(path.join(root,'poster-horizon-v42/browser-clouds-v42.json'))),probes=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry-probes-v43.json'))),raw=fs.readFileSync(path.join(__dirname,'lower-clouds-v43.bin'));
const scene=new T.Scene(),clouds=[],material=new T.MeshBasicMaterial({vertexColors:true,toneMapped:false});
for(let i=0;i<5;i++){const g=new T.SphereGeometry(1,8,6);clouds.push(g);const m=new T.Mesh(g,material);m.name='Main cloud '+i;scene.add(m);}
for(const name of previous.replaces){const g=new T.BufferGeometry();clouds.push(g);const m=new T.Mesh(g,material);m.name=name;scene.add(m);}
for(let i=0;i<14;i++)scene.add(new T.Mesh(clouds[2+i%3],material));
const requested=[];const sandbox={Promise,Error,Map,Set,Float32Array,Uint32Array,fetch:async url=>{requested.push(url);const file=path.resolve(root,'viewer',url);assert(file.startsWith(root+path.sep));const b=fs.readFileSync(file);return{ok:true,json:async()=>JSON.parse(b.toString()),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}};vm.createContext(sandbox);
for(const file of [path.join(root,'poster-horizon-v42/browser-clouds.js'),path.join(__dirname,'browser-clouds.js')])vm.runInContext(fs.readFileSync(file,'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterHorizon42(T,scene,evidence,clouds);const retained=scene.children.slice(),retainedGeometry=retained.map(m=>m.geometry),retainedMatrix=retained.map(m=>m.matrixWorld.clone());const before=clouds.slice();await sandbox.applyPosterLowerClouds43(T,scene,evidence,clouds);
 assert.equal(clouds.length,35);assert.equal(scene.children.length,49);let triangles=0,maxWorldError=0;
 for(let i=0;i<retained.length;i++){assert.strictEqual(scene.children[i],retained[i]);assert.strictEqual(retained[i].geometry,retainedGeometry[i]);assert(retained[i].matrixWorld.equals(retainedMatrix[i]));}
 for(let i=0;i<before.length;i++)assert.strictEqual(clouds[i],before[i]);
 for(const [index,q] of spec.clouds.entries()){
  const mesh=scene.getObjectByName(q.name);assert(mesh);assert.strictEqual(mesh.material,material);assert.strictEqual(mesh.geometry,clouds[32+index]);assert(!mesh.matrixAutoUpdate);
  for(const [attribute,key] of [['position','positions'],['normal','normals'],['color','colors']]){const a=mesh.geometry.attributes[attribute].array;assert.equal(a.length,q.vertices*3);for(let i=0;i<a.length;i++)assert.equal(a[i],raw.readFloatLE(q[key].byteOffset+i*4));}
  const indices=mesh.geometry.index.array;for(let i=0;i<indices.length;i++)assert.equal(indices[i],raw.readUInt32LE(q.indices.byteOffset+i*4));triangles+=indices.length/3;
  for(const p of probes[q.name]){const pos=new T.Vector3().fromBufferAttribute(mesh.geometry.attributes.position,p.index).applyMatrix4(mesh.matrixWorld);const error=Math.max(Math.abs(pos.x-p.nativeWorld[0]),Math.abs(pos.y-p.nativeWorld[2]),Math.abs(pos.z+p.nativeWorld[1]));maxWorldError=Math.max(error,maxWorldError);assert(error<3e-5);}
 }
 assert.equal(triangles,spec.triangles);const html=fs.readFileSync(path.join(root,'viewer/poster-v43.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(m[2].trim()){new vm.Script(m[2]);scripts++;}
 assert(html.includes('await applyPosterHorizon42(T,scene,root,cloudGeometries)'));assert(html.includes('await applyPosterLowerClouds43(T,scene,root,cloudGeometries)'));assert(!html.includes('await applyPosterClouds41(T,scene,root,cloudGeometries)'));assert(html.includes('applyPosterWater40(T,water,root,posterWaterSpec40)'));assert(html.includes('suzume-poster-view-v43'));assert.equal(requested.length,4);
 const report={revision:43,nativeSha256:spec.nativeSha256,threeRevision:T.REVISION,inlineScriptsParsed:scripts,addedClouds:3,triangles,positionsNormalsColorsAndIndicesMatchExportExactly:true,nativeWorldProbeMaximumErrorMeters:maxWorldError,worldTransformsVerified:true,existingCloudObjectsGeometriesMatricesPreserved:true,originalMaterialReused:true,cloudInspectionReferencesUpdated:true,scope:'Three.js geometry loading in Node and inline script parsing. No browser or GPU execution.',browserRuntimeVerified:false};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v43.json'),JSON.stringify(report,null,2));console.log('LOWER_CLOUD_43_BROWSER_DATA_VERIFIED',triangles,maxWorldError);
})().catch(e=>{console.error(e);process.exitCode=1;});
