const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js'));
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-clouds-v42.json'))),probes=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry-probes-v42.json'))),raw=fs.readFileSync(path.join(__dirname,'clouds-v42.bin'));
const scene=new T.Scene(),clouds=[],material=new T.MeshBasicMaterial({vertexColors:true,toneMapped:false}),oldMeshes=[];let disposed=0;const requested=[];
for(let i=0;i<5;i++){const g=new T.SphereGeometry(1,8,6);clouds.push(g);const m=new T.Mesh(g,material);m.name='Unchanged main cloud '+i;scene.add(m);}
const untouched=clouds.slice();
for(const name of spec.replaces){const g=new T.BufferGeometry();g.addEventListener('dispose',()=>disposed++);clouds.push(g);const m=new T.Mesh(g,material);m.name=name;scene.add(m);oldMeshes.push(m);}
const surround=[];for(let i=0;i<14;i++){const m=new T.Mesh(untouched[2+i%3],material);scene.add(m);surround.push(m);}
const sandbox={Promise,Error,Map,Set,Float32Array,Uint32Array,fetch:async url=>{requested.push(url);const file=path.resolve(root,'viewer',url);assert(file.startsWith(__dirname+path.sep));const b=fs.readFileSync(file);return{ok:true,json:async()=>JSON.parse(b.toString()),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-clouds.js'),'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterHorizon42(T,scene,evidence,clouds);assert.equal(disposed,28);assert.equal(clouds.length,32);assert.equal(scene.children.length,46);let triangles=0,maxWorldError=0;
 for(const mesh of oldMeshes)assert.strictEqual(mesh.parent,null);
 for(const [index,q] of spec.clouds.entries()){
  const mesh=scene.getObjectByName(q.name);assert(mesh);assert.strictEqual(mesh.material,material);assert.strictEqual(mesh.geometry,clouds[index+5]);assert(!mesh.matrixAutoUpdate);
  for(const [attribute,key] of [['position','positions'],['normal','normals'],['color','colors']]){const a=mesh.geometry.attributes[attribute].array;assert.equal(a.length,q.vertices*3);for(let i=0;i<a.length;i++)assert.equal(a[i],raw.readFloatLE(q[key].byteOffset+i*4));}
  const indices=mesh.geometry.index.array;assert(indices instanceof Uint32Array);for(let i=0;i<indices.length;i++)assert.equal(indices[i],raw.readUInt32LE(q.indices.byteOffset+i*4));triangles+=indices.length/3;
  for(const p of probes[q.name]){const pos=new T.Vector3().fromBufferAttribute(mesh.geometry.attributes.position,p.index).applyMatrix4(mesh.matrixWorld);const err=Math.max(Math.abs(pos.x-p.nativeWorld[0]),Math.abs(pos.y-p.nativeWorld[2]),Math.abs(pos.z+p.nativeWorld[1]));maxWorldError=Math.max(maxWorldError,err);assert(err<3e-5);}
 }
 assert.equal(triangles,spec.triangles);for(let i=0;i<5;i++)assert.strictEqual(clouds[i],untouched[i]);for(let i=0;i<14;i++)assert.strictEqual(surround[i].geometry,untouched[2+i%3]);
 const html=fs.readFileSync(path.join(root,'viewer/poster-v42.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(m[2].trim()){new vm.Script(m[2]);scripts++;}
 assert(html.includes('await applyPosterHorizon42(T,scene,root,cloudGeometries)'));assert(!html.includes('await applyPosterClouds41(T,scene,root,cloudGeometries)'));assert(html.includes('applyPosterWater40(T,water,root,posterWaterSpec40)'));assert(html.includes('await applyPosterSteel39(T,scene,root)'));assert(html.includes('suzume-poster-view-v42'));assert(!html.includes('applyMovieTerrain31'));assert.equal(requested.length,2);assert(requested.every(url=>url.includes('poster-horizon-v42/')));
 const report={revision:42,threeRevision:T.REVISION,inlineScriptsParsed:scripts,removedClouds:28,loadedClouds:27,triangles,positionsNormalsColorsAndIndicesMatchExportExactly:true,nativeWorldProbeMaximumErrorMeters:maxWorldError,worldTransformsVerified:true,originalMaterialsPreserved:true,mainCloudGeometriesUntouched:true,surroundingCloudGeometriesUntouched:true,inspectionGeometryReferencesUpdated:true,onlyFinalCloudPayloadRequested:true,scope:'Actual Three.js mesh import and JavaScript parsing in Node. No browser or GPU execution.',browserRuntimeVerified:false};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v42.json'),JSON.stringify(report,null,2));console.log('HORIZON_42_BROWSER_GEOMETRY_VERIFIED',triangles,maxWorldError);
})().catch(e=>{console.error(e);process.exitCode=1;});
