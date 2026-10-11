const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.dirname(__dirname),T=require(path.join(root,'viewer/three.min.js'));
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-steel-v39.json'))),source=JSON.parse(fs.readFileSync(path.join(__dirname,'source-steel-v39.json')));
const scene=new T.Scene(),originals=[];let disposed=0;
for(const [index,q] of source.entries()){
  const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(q.vertices*3),3));g.addEventListener('dispose',()=>disposed++);
  const material=new T.MeshStandardMaterial({color:0x887755});const mesh=new T.Mesh(g,material);mesh.name='Broken radial dome steelwork solid mesh';scene.add(mesh);originals.push({q,mesh,material});
}
const untouched=new T.Mesh(new T.BoxGeometry(1,1,1),new T.MeshStandardMaterial());scene.add(untouched);
const sandbox={Float32Array,Map,Error,fetch:async url=>{
  const file=path.resolve(root,'viewer',url);assert(file.startsWith(__dirname));const bytes=fs.readFileSync(file);
  return {ok:true,json:async()=>JSON.parse(bytes.toString()),arrayBuffer:async()=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)};
}};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'browser-steel.js'),'utf8'),sandbox);
(async()=>{
  const evidence={};await sandbox.applyPosterSteel39(T,scene,evidence);assert.equal(disposed,4);assert(scene.children.includes(untouched));
  const group=scene.getObjectByName('Reference-observed poster steel v39');assert(group&&group.children.length===8);const binary=fs.readFileSync(path.join(__dirname,'steel-v39.bin'));let triangles=0;
  for(const q of spec.buckets){
    const mesh=group.getObjectByName('Poster steel '+q.key+' v39');assert(mesh.castShadow&&mesh.receiveShadow);const p=mesh.geometry.attributes.position.array,n=mesh.geometry.attributes.normal.array,uv=mesh.geometry.attributes.uv.array;
    for(let i=0;i<q.vertexCount;i++)for(let j=0;j<8;j++){const actual=j<3?p[i*3+j]:j<6?n[i*3+j-3]:uv[i*2+j-6];assert.equal(actual,binary.readFloatLE(q.byteOffset+(i*8+j)*4));}
    if(q.originalVertexCount)assert.strictEqual(mesh.material,originals.find(x=>x.q.vertices===q.originalVertexCount).material);
    triangles+=q.vertexCount/3;
  }
  assert.equal(triangles,65964);assert.equal(evidence.posterSteelEvidence39.closedMembers,16);
  const html=fs.readFileSync(path.join(root,'viewer/poster-v39.html'),'utf8');let parsed=0;
  for(const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)){if(match[2].trim()){new vm.Script(match[2]);parsed++;}}
  assert(html.includes("let state={open:false,motion:false,azimuth:posterComposition.azimuth"));assert(html.includes('suzume-poster-view-v39'));assert(!html.includes('applyMovieTerrain31'));
  fs.writeFileSync(path.join(__dirname,'browser-code-verification-v39.json'),JSON.stringify({revision:39,threeVersion:T.REVISION,inlineScriptsParsed:parsed,buckets:8,triangles,positionsNormalsUVVerifiedExactly:true,originalMaterialsPreserved:true,unrelatedSceneObjectsPreserved:true,scope:'Pure geometry import and script parsing using Three.js. No browser or GPU execution.',browserRuntimeVerified:false},null,2));
  console.log('POSTER_39_BROWSER_GEOMETRY_VERIFIED',triangles);
})().catch(err=>{console.error(err);process.exitCode=1;});
