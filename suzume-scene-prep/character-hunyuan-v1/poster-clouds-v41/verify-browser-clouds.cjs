const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js'));
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-clouds-v41.json'))),probes=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry-probes-v41.json'))),raw=fs.readFileSync(path.join(__dirname,'clouds-v41.bin'));
const scene=new T.Scene(),clouds=[],material=new T.MeshBasicMaterial({vertexColors:true,toneMapped:false}),oldMeshes=[];let disposed=0;
for(let i=0;i<5;i++){const g=new T.SphereGeometry(1,8,6);clouds.push(g);const m=new T.Mesh(g,material);m.name='Unchanged main cloud '+i;scene.add(m);}
const untouched=clouds.slice();
for(const q of spec.clouds){const g=new T.BufferGeometry();g.addEventListener('dispose',()=>disposed++);clouds.push(g);const m=new T.Mesh(g,material);m.name=q.name;scene.add(m);oldMeshes.push(m);}
const sandbox={Promise,Error,Float32Array,Uint32Array,fetch:async url=>{const file=path.resolve(root,'viewer',url);assert(file.startsWith(__dirname));const b=fs.readFileSync(file);return{ok:true,json:async()=>JSON.parse(b.toString()),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-clouds.js'),'utf8'),sandbox);
(async()=>{
 const evidence={};await sandbox.applyPosterClouds41(T,scene,evidence,clouds);assert.equal(disposed,28);let triangles=0,maxWorldError=0;
 for(const q of spec.clouds){
  const mesh=scene.getObjectByName(q.name);assert.strictEqual(mesh,oldMeshes[q.index]);assert.strictEqual(mesh.material,material);assert.strictEqual(mesh.geometry,clouds[q.index+5]);assert(!mesh.matrixAutoUpdate);
  for(const [attribute,key] of [['position','positions'],['normal','normals'],['color','colors']]){const a=mesh.geometry.attributes[attribute].array;assert.equal(a.length,q.vertices*3);for(let i=0;i<a.length;i++)assert.equal(a[i],raw.readFloatLE(q[key].byteOffset+i*4));}
  const indices=mesh.geometry.index.array;assert(indices instanceof Uint32Array);for(let i=0;i<indices.length;i++)assert.equal(indices[i],raw.readUInt32LE(q.indices.byteOffset+i*4));triangles+=indices.length/3;
  for(const p of probes[q.index]){const pos=new T.Vector3().fromBufferAttribute(mesh.geometry.attributes.position,p.index).applyMatrix4(mesh.matrixWorld);const err=Math.max(Math.abs(pos.x-p.nativeWorld[0]),Math.abs(pos.y-p.nativeWorld[2]),Math.abs(pos.z+p.nativeWorld[1]));maxWorldError=Math.max(maxWorldError,err);assert(err<3e-5);}
 }
 assert.equal(triangles,spec.triangles);for(let i=0;i<5;i++)assert.strictEqual(clouds[i],untouched[i]);
 const html=fs.readFileSync(path.join(root,'viewer/poster-v41.html'),'utf8');let scripts=0;for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g))if(m[2].trim()){new vm.Script(m[2]);scripts++;}
 assert(html.includes('await applyPosterClouds41(T,scene,root,cloudGeometries)'));assert(html.includes('applyPosterWater40(T,water,root,posterWaterSpec40)'));assert(html.includes('await applyPosterSteel39(T,scene,root)'));assert(html.includes('suzume-poster-view-v41'));assert(!html.includes('applyMovieTerrain31'));
 const report={revision:41,threeRevision:T.REVISION,inlineScriptsParsed:scripts,replacedClouds:28,triangles,positionsNormalsColorsAndIndicesMatchExportExactly:true,nativeWorldProbeMaximumErrorMeters:maxWorldError,worldTransformsVerified:true,originalMaterialsPreserved:true,mainCloudGeometriesUntouched:true,inspectionGeometryReferencesUpdated:true,scope:'Actual Three.js mesh import and JavaScript parsing in Node. No browser or GPU execution.',browserRuntimeVerified:false};fs.writeFileSync(path.join(__dirname,'browser-code-verification-v41.json'),JSON.stringify(report,null,2));console.log('CLOUD_41_BROWSER_GEOMETRY_VERIFIED',triangles,maxWorldError);
})().catch(e=>{console.error(e);process.exitCode=1;});
